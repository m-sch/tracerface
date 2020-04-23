from pathlib import Path
from pytest import raises
from queue import Empty
from unittest.mock import Mock, patch

from model.model import Model
from model.parse_stack import Stack
from model.trace_utils import STACK_END_PATTERN


def test_empty_model():
    persistence = Mock()
    model = Model(persistence)

    assert model._persistence == persistence


def test_get_nodes_gets_nodes_from_persistence():
    persistence = Mock()
    model = Model(persistence)

    model.get_nodes()

    persistence.get_nodes.assert_called_once()


def test_get_edges_gets_edges_from_persistence():
    persistence = Mock()
    model = Model(persistence)

    model.get_edges()

    persistence.get_edges.assert_called_once()


def test_yellow_count_gets_range_from_persistence():
    persistence = Mock()
    model = Model(persistence)

    model.yellow_count()

    persistence.get_yellow.assert_called_once()


def test_red_count_gets_range_from_persistence():
    persistence = Mock()
    model = Model(persistence)

    model.red_count()

    persistence.get_red.assert_called_once()


def test_max_count_gets_with_no_nodes():
    persistence = Mock()
    persistence.get_nodes.return_value = {}
    model = Model(persistence)

    assert model.max_count() == 0


def test_max_count_gets_with_nodes():
    persistence = Mock()
    persistence.get_nodes.return_value = {
        'dummy_hash1': {'name': 'dummy_name1', 'source': 'dummy_source1', 'call_count': 2},
        'dummy_hash2': {'name': 'dummy_name2', 'source': 'dummy_source2', 'call_count': 5}
    }
    model = Model(persistence)

    assert model.max_count() == 5


def test_set_range_calls_persistence_with_right_params():
    persistence = Mock()
    model = Model(persistence)

    model.set_range('dummy_yellow', 'dummy_red')

    persistence.update_colors.assert_called_once()
    persistence.update_colors.assert_called_with('dummy_yellow', 'dummy_red')


def test_init_colors():
    persistence = Mock()
    model = Model(persistence)
    model.max_count = Mock(return_value=8)

    model.init_colors()

    assert model.max_count.call_count == 2
    persistence.update_colors.assert_called_once()
    persistence.update_colors.assert_called_with(3, 5)


def test_empty_model():
    persistence = Mock()
    model = Model(persistence)

    assert not model._thread_enabled
    assert model._thread_error == None
    assert model._persistence == persistence


def test_monitor_tracing_without_thread_enabled_with_process_alive():
    process = Mock()
    queue = Mock()
    model = Model(Mock())
    process.is_alive = Mock(return_value=True)

    model.monitor_tracing(queue, process)

    process.is_alive.assert_called()
    process.terminate.assert_called()
    assert not queue.get_nowait.called


def test_monitor_tracing_without_thread_enabled_without_process_alive():
    model = Model(Mock())
    queue = Mock()
    process = Mock()
    process.is_alive = Mock(return_value=False)

    model.monitor_tracing(queue, process)

    process.is_alive.assert_called()
    assert not process.terminate.called
    assert not queue.get_nowait.called


def test_monitor_tracing_with_thread_enabled_without_process_alive():
    model = Model(Mock())
    model._thread_enabled = True
    queue = Mock()
    process = Mock()
    process.is_alive = Mock(return_value=False)

    model.monitor_tracing(queue, process)

    assert model._thread_error == 'Tracing stopped unexpectedly'


@patch('model.model.parse_stack', return_value=Stack(nodes='dummy_nodes', edges='dummy_edges'))
def test_monitor_tracing_with_thread_enabled_with_process_alive_at_stack_end(parse_stack):
    def side_effect(*argv):
        model._thread_enabled = False
        return True

    persistence = Mock()
    queue = Mock()
    process = Mock()

    persistence.get_nodes.return_value = {}
    queue.get_nowait.return_value = STACK_END_PATTERN
    process.is_alive = Mock(side_effect=side_effect)

    model = Model(persistence)
    model._thread_enabled = True

    model.monitor_tracing(queue, process)

    persistence.load_edges.assert_called_with('dummy_edges')
    persistence.load_nodes.assert_called_with('dummy_nodes')


@patch('model.model.parse_stack', return_value=Stack(nodes='dummy_nodes', edges='dummy_edges'))
def test_monitor_tracing_with_thread_enabled_with_process_alive_at_middle_of_stack(parse_stack):
    def side_effect(*argv):
        model._thread_enabled = False
        return True

    persistence = Mock()
    queue = Mock()
    process = Mock()

    persistence.get_nodes.return_value = {}
    queue.get_nowait.return_value = 'dummy value'
    process.is_alive = Mock(side_effect=side_effect)

    model = Model(persistence)
    model._thread_enabled = True

    model.monitor_tracing(queue, process)

    assert not persistence.load_edges.called


def test_monitor_tracing_handles_empty_exception():
    def side_effect(*argv):
        model._thread_enabled = False
        return True

    model = Model(Mock())
    model._thread_enabled = True
    queue = Mock()
    queue.get_nowait.side_effect = Empty
    process = Mock()
    process.is_alive = Mock(side_effect=side_effect)

    model.monitor_tracing(queue, process)

    process.terminate.assert_called()


@patch('model.model.Thread')
@patch('model.model.TraceProcess')
def test_start_trace(process, thread):
    model = Model(Mock())

    model.start_trace(['dummy', 'functions'])

    assert model._thread_error == None
    assert model._thread_enabled
    thread.assert_called_once()
    thread.return_value.start.assert_called_once()
    process.assert_called_once()
    process.return_value.start.assert_called_once()


def test_start_trace_without_functions():
    model = Model(Mock())
    model.start_trace([])

    assert model._thread_error == 'No functions to trace'


def test_stop_trace():
    model = Model(Mock())
    model._thread_enabled = True
    model.init_colors = Mock()

    model.stop_trace()

    assert not model._thread_enabled
    model.init_colors.assert_called_once()


def test_thread_error_returns_error():
    model = Model(Mock())
    model._thread_error = 'Dummy Error'

    assert model.thread_error() == 'Dummy Error'


def test_trace_active_returns_thread_enabled():
    model = Model(Mock())
    model._thread_enabled = True

    assert model.trace_active()


def test_load_output():
    test_file_path = Path.cwd().joinpath(
        'tests', 'integration', 'resources', 'test_static_output'
    )
    text = test_file_path.read_text()
    persistence = Mock()
    persistence.get_nodes.return_value = {}
    model = Model(persistence)

    model.load_output(text)

    assert persistence.load_edges.call_count == 8
    assert persistence.load_nodes.call_count == 8