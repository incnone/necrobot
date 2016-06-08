import subprocess
import time

run_again = True
last_reboot_time = 0

while run_again:
    run_again = False
    last_reboot_time = time.clock()
    necrobot_proc = subprocess.Popen('cmd /k python main.py')
    try:
        necrobot_proc.wait()
        return_code = necrobot_proc.returncode
        print("Necrobot process exited without exceptions; return code {0}".format(return_code))
        run_again = (return_code != 0)
    except Exception as e:
        print("HTTPException occurred while running the Necrobot:")
        print(e)
        run_again = True

    if run_again:
        if time.clock() - last_reboot_time < 60:
            print("It has been less than one minute since the last restart attempt, so necroguard is shutting down.")
            run_again = False
        else:
            print("Attempting to restart.")


    
