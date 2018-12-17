from byexample.concern import Concern
import coverage

class ByexampleCoverage(Concern):
    target = 'byexample-coverage'

    def __init__(self, **unused):
        pass

    def start(self, examples, runners, filepath, options):
        self.runners = runners
        self.options = options
        for runner in runners:
            if runner.language == 'python':
                coverage_start_code = r'''
from coverage import Coverage as _cov_class
_cov_instance = _cov_class(source=['byexample'], auto_data=True)
_cov_instance.start()
'''
                runner._exec_and_wait(coverage_start_code, options, timeout=10)
                break


    def finish(self, *args):
        for runner in self.runners:
            if runner.language == 'python':
                coverage_end_code = r'''
_cov_instance.stop()
_cov_instance.save()
'''
                runner._exec_and_wait(coverage_end_code, self.options, timeout=10)
                break
