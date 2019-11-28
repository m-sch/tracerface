from threading import Thread

import pexpect

from model.base import BaseModel
from model.utils import (
    extract_config,
    flatten_trace_dict,
    parse_stack,
    ProcessException
)


class DynamicModel(BaseModel):
    def __init__(self, configuration):
        super().__init__(configuration)
        self._thread_enabled = False
        self._thread_error = None
        self._process_error = None

    def _process_output(self, child, stack):
        try:
            child.expect('\n', timeout=1)
        except pexpect.TIMEOUT:
            pass
        raw = child.before
        call = raw.decode("utf-8")
        if call == '\r':
            graph = parse_stack(stack)
            self._persistence.load_edges(graph.edges)
            self._persistence.load_nodes(graph.nodes)
            self.init_colors()
            stack.clear()
        else:
            stack.append(call)

    def _run_command(self, cmd):
        try:
            child = pexpect.spawn(cmd, timeout=None)
            stack = []
            while self._thread_enabled:
                self._process_output(child, stack)
            child.close()
        except pexpect.EOF:
            pass
        except pexpect.exceptions.ExceptionPexpect as e:
            self._thread_error = str(e)
        finally:
            self._thread_enabled = False

    def trace_dict(self, dict_to_trace):
        try:
            functions = flatten_trace_dict(dict_to_trace)
            self.start_trace(functions)
        except ProcessException as e:
            self._process_error = str(e)

    def trace_yaml(self, config_path):
        try:
            functions = extract_config(config_path)
            self.start_trace(functions)
        except ProcessException as e:
            self._process_error = str(e)

    def start_trace(self, functions):
        self._thread_error = None
        self._process_error = None
        self._thread_enabled = True
        self._persistence.clear()
        cmd = [self._configuration.get_command(), '-UK'] + ['\'{}\''.format(function) for function in functions]
        thread = Thread(target=self._run_command, args=[' '.join(cmd)])
        thread.start()

    def stop_trace(self):
        self._thread_enabled = False
        self.init_colors()

    def thread_error(self):
        return self._thread_error

    def process_error(self):
        return self._process_error

    def trace_active(self):
        return self._thread_enabled
