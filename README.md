# 🎈 Blank app template
# 🎈 Charlotte's Super Scheduler

A simple Streamlit app for a manager to create schedules for her team !
Uses ortools to generate a model for the planning based on boolean "shifts" value indicating the role taken by an employee at a specific time. (True = "A is doing this job at this moment", False="A is not doing this job at this moment").


Constraints in python corresponding to constraints in the planning are added to the model, and a solver is used to find a configuration of variables that enforces the constraints.


There are two different teams with different roles.

Why is it cool ? 
- We can add / remove member of the teams and the schedule is automatically upsdated.
- We can add / remove / update days where the team member is working remotely.
- We can add / remove / update days where the team member is on leave.
- We can select the constraints which have to be enforced.

Limitations:
Changing or adding a new constraint is a time-intensive tasks, as it has to be "hardcoded" in the python code and can sometimes result in conflicting constraints, which renders the model insolvable.

### How to run it on your own machine

1. Install the requirements

   ```
   $ pip install -r requirements.txt
   ```

2. Run the app

   ```
   $ streamlit run streamlit_app.py
   ```
