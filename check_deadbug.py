from app.exercises.data import EXERCISES
ex = EXERCISES.get('dead_bug')
with open('deadbug_check.txt', 'w', encoding='utf-8') as f:
    f.write('dead_bug status: ' + ex.description_status + '\n')
    f.write('summary: ' + ex.description.summary[:60] + '\n')
    f.write('execution len: ' + str(len(ex.description.execution)) + '\n')
    f.write('cues len: ' + str(len(ex.description.cues)) + '\n')
    f.write('common_mistakes len: ' + str(len(ex.description.common_mistakes)) + '\n')
    f.write('breathing: ' + ex.description.breathing[:60] + '\n')
    f.write('description_status: ' + ex.description_status + '\n')
