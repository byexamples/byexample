from byexample.concern import Concern
import coverage

class ByexampleCoverage(Concern):
    target = 'byexample-coverage'

    def __init__(self, **unused):
        pass

    def start_run(self, examples, interpreters, filepath):
        self.interpreters = interpreters
        for interpreter in interpreters:
            if interpreter.language == 'python':
                coverage_start_code = r'''
from coverage import Coverage as _cov_class
_cov_instance = _cov_class(auto_data=True)
_cov_instance.start()
'''
                interpreter._exec_and_wait(coverage_start_code, 10)
                break


    def end_run(self, failed, user_aborted, crashed):
        for interpreter in self.interpreters:
            if interpreter.language == 'python':
                coverage_end_code = r'''
_cov_instance.stop()
_cov_instance.save()
'''
                interpreter._exec_and_wait(coverage_end_code, 10)
                break
