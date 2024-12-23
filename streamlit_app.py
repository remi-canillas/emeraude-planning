import streamlit as st
import pandas as pd
import json
from ortools.sat.python import cp_model


st.title("❇️ Lucille's Super Scheduler 💚")
st.write(
    "Le planning de l'équipe Emeraude !"
)

days = ["Monday",
        "Tuesday",
        "Wednesday",
        "Thursday",
        "Friday"]

with open("employee_planning.json", "r") as employee_file:
    employees_planning = json.load(employee_file)
st.text_input("Quel prénom ?", key="name", placeholder="Charlotte")
st.write("Jours de télétravail:")
day_tt = st.columns(5)
checkbox_dict_tt = {}
for d_idx, day in enumerate(day_tt):
    check_day_tt = day.checkbox(days[d_idx])
    checkbox_dict_tt[days[d_idx]] = check_day_tt

st.write("Jours d'absence:")
day_abs = st.columns(5)
checkbox_dict_abs = {}
for d_idx, day in enumerate(day_abs):
    check_day_abs = day.checkbox(
        days[d_idx], key=days[d_idx]+"_abs", disabled=checkbox_dict_tt[days[d_idx]])
    checkbox_dict_abs[days[d_idx]] = check_day_abs
# Dict pour les rôles de chaque équipe:
role_dict = {"Présentiel": ["Production", "Signature", "IC"],
             "Télétravail": ["Production", "IC"],
             "Absent": ["Absent"]
             }

roles = set(role_dict["Présentiel"] +
            role_dict["Télétravail"] + role_dict["Absent"])
left, right = st.columns(2)

if left.button("Ajouter le collaborateur", icon="➕", use_container_width=True):
    employees_planning[st.session_state.name] = {
        d: "Télétravail" if checkbox_dict_tt[d] else "Absent" if checkbox_dict_abs[d] else "Présentiel" for d in days}
    with open("employee_planning.json", "w") as employee_file:
        json.dump(employees_planning, employee_file)
if right.button("Enlever le collaborateur", icon="➖", use_container_width=True):
    with open("employee_planning.json", "r") as employee_file:
        employees_planning = json.load(employee_file)
    if st.session_state.name in employees_planning:
        employees_planning.pop(st.session_state.name)
        right.markdown(f"{st.session_state.name} enlevé !")
    else:
        right.markdown(f"{st.session_state.name} n'est pas dans la liste !")
    with open("employee_planning.json", "w") as employee_file:
        json.dump(employees_planning, employee_file)

with open("employee_planning.json", "r") as employee_file:
    employees_planning = json.load(employee_file)

employees = list(employees_planning.keys())
st.dataframe(pd.DataFrame(employees_planning), use_container_width=True)
employees_roles = {
    e: {d: role_dict[employees_planning[e][d]]for d in days} for e in employees
}

model = cp_model.CpModel()
shifts = ["AM", "PM"]
schedule = {e:
            {r:
             {d:
              {s: model.new_bool_var(f"schedule_{e}_{r}_{d}_{s}")
               for s in shifts}
              for d in days}
             for r in roles}
            for e in employees}

# Les employés ne peuvent pas faire un rôle qu'on ne leur a pas attribué:
for e in employees:
    for r in roles:
        for d in days:
            for s in shifts:
                if r not in employees_roles[e][d]:
                    model.add(schedule[e][r][d][s] == 0)

# Les employés ne peuvent pas faire deux rôles en même temps
for e in employees:
    for d in days:
        for s in shifts:
            model.add(sum(schedule[e][r][d][s] for r in roles) <= 1)

rule1 = st.checkbox(
    "Il faut toujours que pour chaque demi-journée on ait une personne de Signature et une personne d’IC.", value=True)
if rule1:
    has_sign = {}
    has_ic = {}
    for d in days:
        has_sign[d] = {}
        has_ic[d] = {}
        for s in shifts:
            has_sign[d][s] = {}
            has_ic[d][s] = {}
            model.add(sum(schedule[e]["Signature"][d][s]
                      for e in employees) == 1)
            model.add(sum(schedule[e]["IC"][d][s] for e in employees) == 1)
            for e in employees:
                if employees_planning[e][d] != "Absent":
                    has_sign[d][s][e] = model.new_bool_var(
                        f"has_sign_{d}_{s}_{e}")
                    has_ic[d][s][e] = model.new_bool_var(f"has_ic_{d}_{s}_{e}")
                    model.add(schedule[e]["Signature"][d]
                              [s] == 1).only_enforce_if(has_sign[d][s][e])
                    model.add(schedule[e]["IC"][d][s] ==
                              1).only_enforce_if(has_ic[d][s][e])
                    model.add(schedule[e]["Production"][d][s] == 1).only_enforce_if(
                        ~has_sign[d][s][e]).only_enforce_if(~has_ic[d][s][e])

rule2 = st.checkbox(
    "Il faut que chaque personne ait une journée de prod complète.\n"
    "Il faut que personne n'ait une journée avec que de l'IC.\n", value=True)
if rule2:
    has_full_day_prod = {}
    has_full_day_IC = {}
    is_absent = {}
    for e in employees:
        has_full_day_prod[e] = {
            d:  model.new_bool_var(f"has_full_day_prod_{e}_{d}") for d in days
        }
        has_full_day_IC[e] = {
            d:  model.new_bool_var(f"has_full_day_IC_{e}_{d}") for d in days
        }
        is_absent[e] = {
            d:  model.new_bool_var(f"is_absent_{e}_{d}") for d in days
        }
        for d in days:
            if employees_planning[e][d] == "Absent":
                model.add(sum(schedule[e]["Absent"][d][s]
                          for s in shifts) == 2)
            else:
                model.add(
                    sum(schedule[e]["Production"][d][s] for s in shifts) == 2
                ).only_enforce_if(has_full_day_prod[e][d])
                model.add(
                    sum(schedule[e]["Production"][d][s] for s in shifts) <= 1
                ).only_enforce_if(~has_full_day_prod[e][d])
                model.add(
                    sum(schedule[e]["IC"][d][s] for s in shifts) == 2
                ).only_enforce_if(has_full_day_IC[e][d])
                model.add(
                    sum(schedule[e]["IC"][d][s] for s in shifts) <= 1
                ).only_enforce_if(~has_full_day_IC[e][d])
            model.add(
                sum(has_full_day_prod[e][d] for d in days) >= 1
            )
            model.add(
                sum(has_full_day_IC[e][d] for d in days) == 0
            )

rule3 = st.checkbox(
    "Il faut que les plannings soient équilibrés (Une demi-journée max de différence pour chaque tâches.)", value=True)
if rule3:
    max_nb_shifts = 10
    total_shifts = {}
    min_shifts = {}
    max_shifts = {}
    full_week_employees = [e for e in employees if "Absent" not in [
        employees_planning[e][d] for d in days]]
    for r in [r for r in roles if r != "Absent"]:
        print(r)
        total_shifts[r] = {}
        for e in full_week_employees:
            total_shifts[r][e] = model.new_int_var(
                0, max_nb_shifts, f"total_shifts_c_{e}_{r}")
            model.add(total_shifts[r][e] == sum(
                schedule[e][r][d][s] for d in days for s in shifts))
        min_shifts[r] = model.new_int_var(
            0, max_nb_shifts, f"min_shifts_c_{r}")
        model.add_min_equality(
            min_shifts[r], [total_shifts[r][e] for e in full_week_employees])
        max_shifts[r] = model.new_int_var(
            0, max_nb_shifts, f"max_shifts_c_{r}")
        model.add_max_equality(
            max_shifts[r], [total_shifts[r][e] for e in full_week_employees])
        model.add(max_shifts[r] - min_shifts[r] <= 1)


solver = cp_model.CpSolver()
solver.solve(model)
status = solver.solve(model)
if status == cp_model.OPTIMAL or status == cp_model.FEASIBLE:
    st.write("Emploi du temps généré !")
    left, right = st.columns(2)
    left.write("🔵 = Production")
    right.write("🟡 = Signature")
    left.write("🟢 = Intercom")
    right.write("🚫 = Absent")

    data_list = []
    for e in employees:
        for d in days:
            for s in shifts:
                role = "🟡" if solver.value(schedule[e]["Signature"][d][s]) == 1 else "🔵" if (solver.value(schedule[e]["Production"][d][s])
                                                                                             == 1) else "🟢" if solver.value(schedule[e]["IC"][d][s]) == 1 else "🚫" if solver.value(schedule[e]["Absent"][d][s]) == 1 else None
                # role += "t" if employees_planning[e][d] == "Télétravail" else "" if employees_planning[e][d] == "Absent"  else "o"
                data_list.append(
                    {"employee": e, "day": d, "shift": s, "role": role})
    schedule_df = pd.DataFrame(data_list).sort_values(by=["day", "employee"])
    pivot_data = schedule_df.pivot_table(
        index='employee',
        columns=['day', 'shift'],
        values='role',
        aggfunc='first'
    ).reindex(['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday'], axis=1, level=0)
    # custom_order =
    # pivot_data['day'] = pd.Categorical(pivot_data['day'], categories=custom_order, ordered=True)
    # pivot_data = pivot_data.sort_values(by=['day','shift'])
    st.dataframe(pivot_data, use_container_width=True,)

    count_dict_list = []
    for employee, employee_df in schedule_df.groupby(by="employee"):
        shift_counts = employee_df["role"].value_counts()
        count_dict = {"employee": employee}
        for role, role_count in zip(shift_counts.index, shift_counts.values):
            count_dict[role] = role_count
        count_dict_list.append(count_dict)
    count_df = pd.DataFrame(count_dict_list)
    st.write("Compte total:")
    st.write(count_df)
else:
    st.write("Pas d'emploi du temps possible  :(")
