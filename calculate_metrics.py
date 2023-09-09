from base45reflex.SQLModels import Exercise, User, UserProgramHistory, Workout, WorkoutSet, UserWorkoutMetrics
import pandas as pd
from sqlmodel import Session, create_engine, select
from rxconfig import ENVIRONMENT


def calculate_metrics(user: User, session: Session):
    program_history_statement = UserProgramHistory.select.filter(UserProgramHistory.user_id == user.id)
    program_history = session.scalars(program_history_statement).all()
    for program in program_history:
        workout_statement = (Workout.select.filter(Workout.user_id == user.id)
                             .filter(Workout.date <= program.end_date)
                             .filter(Workout.date >= program.start_date))
        workout_list = session.scalars(workout_statement).all()
        if not workout_list:
            continue
        for workout in workout_list:
            set_statement = select(WorkoutSet, Exercise).join(Exercise).where(WorkoutSet.workout_id == workout.id)
            set_list = sess.exec(set_statement).all()
            for ex_set in set_list:
                temp_set = ex_set[0]
                exercise = ex_set[1]
                load_value = temp_set.weight * temp_set.num_sets
                load = UserWorkoutMetrics(set_id=temp_set.id, user_id=user.id, metric='TotalLoad', date=workout.date,
                                          exercise=exercise.name, value=load_value, unit_id=temp_set.unit_id)
                avg_rpe = UserWorkoutMetrics(set_id=temp_set.id, user_id=user.id, value=temp_set.avg_rpe,
                                             date=workout.date, exercise=exercise.name, metric='AvgRPE')
                avg_reps = UserWorkoutMetrics(set_id=temp_set.id, user_id=user.id, metric='AvgRepsPerSet',
                                              date=workout.date, exercise=exercise.name,
                                              value=temp_set.reps/temp_set.num_sets)
                sess.add(load)
                sess.add(avg_rpe)
                sess.add(avg_reps)
                sess.commit()


if __name__ == "__main__":
    if ENVIRONMENT == "DEV":
        db_url = "sqlite:///reflex_dev.db"
    else:
        db_url = "sqlite:///reflex.db"

    engine = create_engine(db_url)

    with Session(engine) as sess:
        user_list = sess.scalars(User.select.filter()).all()

        for user in user_list:
            calculate_metrics(user, sess)
