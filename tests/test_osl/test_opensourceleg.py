import csv
import time

import numpy as np
import pytest

import opensourceleg.constants as constants
import opensourceleg.utilities as utilities
from opensourceleg.actuators import (
    CurrentMode,
    ImpedanceMode,
    PositionMode,
    VoltageMode,
)
from opensourceleg.joints import Joint
from opensourceleg.loadcell import Loadcell
from opensourceleg.logger import Logger
from opensourceleg.osl import OpenSourceLeg
from opensourceleg.state_machine import Event, State, StateMachine
from opensourceleg.units import DEFAULT_UNITS, UnitsDefinition
from opensourceleg.utilities import SoftRealtimeLoop
from tests.test_actuators.test_dephyactpack import Data
from tests.test_joints.test_joint import (
    MockJoint,
    joint_mock,
    joint_patched,
    patch_joint,
    patch_sleep,
    patch_time_time,
)
from tests.test_loadcell.test_loadcell import (
    MockStrainAmp,
    loadcell_mock,
    loadcell_patched,
    patch_loadcell,
)
from tests.test_logger.test_logger import Simple_Class
from tests.test_state_machine.test_state_machine import mock_time


# Test the OpenSourceLeg constructor
def test_opensourceleg_init(mock_time):
    # Create a new OpenSourceLeg
    test_osl = OpenSourceLeg()

    # Check that the OpenSourceLeg was initialized properly
    assert test_osl._frequency == 200
    assert test_osl._has_knee == False
    assert test_osl._has_ankle == False
    assert test_osl._has_loadcell == False
    assert test_osl._has_tui == False
    assert test_osl._has_sm == False
    assert test_osl._is_homed == False
    assert test_osl._knee == None
    assert test_osl._ankle == None
    assert test_osl._loadcell == None
    assert test_osl._log_data == False
    # assert test_osl.clock
    assert test_osl._units == DEFAULT_UNITS
    assert test_osl.tui == None
    assert test_osl.state_machine == None
    assert test_osl._timestamp == 1.0


# Test the static method to create a new OpenSourceLeg
def test_osl_create(mock_time):
    OpenSourceLeg.get_instance()
    assert OpenSourceLeg._instance == None


# Test the OpenSourceLeg __enter__ method
def test_osl_enter(
    mock_get_active_ports, joint_patched: Joint, loadcell_patched: Loadcell, patch_sleep
):
    # Create a new OpenSourceLeg
    test_osl_ent = OpenSourceLeg()
    test_osl_ent.log = Logger(file_path="tests/test_osl/test_osl_ent")
    test_osl_ent.log.set_stream_level("DEBUG")
    test_osl_ent.add_joint(name="knee")
    test_osl_ent.add_joint(name="ankle")
    test_osl_ent.add_loadcell()
    test_osl_ent._knee._data = Data(
        batt_volt=10,
        batt_curr=10,
        mot_volt=10,
        mot_cur=10,
        mot_ang=10,
        ank_ang=10,
        mot_vel=10,
        mot_acc=10,
        ank_vel=10,
        temperature=10,
        genvar_0=10,
        genvar_1=10,
        genvar_2=10,
        genvar_3=10,
        genvar_4=10,
        genvar_5=10,
        accelx=10,
        accely=10,
        accelz=10,
        gyrox=10,
        gyroy=10,
        gyroz=10,
    )
    assert test_osl_ent._knee._data.batt_volt == 10
    test_osl_ent.__enter__()
    assert test_osl_ent._knee._data.batt_volt == 40
    with open("tests/test_osl/test_osl_ent.log", "r") as f1:
        contents1 = f1.read()
        assert (
            "INFO: [LOADCELL] Initiating zeroing routine, please ensure that there is no ground contact force."
            in contents1
        )


# Unfnished: tui
# Test the OpenSourceLeg __exit__ method
def test_osl_exit(mock_get_active_ports, joint_patched: Joint, mock_time, patch_sleep):
    # Create a new OpenSourceLeg
    test_osl_ex = OpenSourceLeg()
    test_osl_ex.log = Logger(file_path="tests/test_osl/test_osl_ex")
    test_osl_ex.log.set_stream_level("DEBUG")
    test_osl_ex.add_state_machine()
    test_osl_ex.state_machine._current_state = State(name="test_state")
    test_osl_ex._is_sm_running = True
    test_osl_ex.add_joint(name="knee")
    test_osl_ex._knee._mode = CurrentMode(device=test_osl_ex._knee)
    test_osl_ex.add_joint(name="ankle")
    test_osl_ex._ankle._mode = ImpedanceMode(device=test_osl_ex._ankle)
    test_osl_ex.__exit__(type=None, value=None, tb=None)
    assert test_osl_ex._knee._mode == VoltageMode(device=test_osl_ex._knee)
    assert test_osl_ex._ankle._mode == VoltageMode(device=test_osl_ex._ankle)
    assert test_osl_ex.state_machine._exited == True


# Test the OpenSourceLeg __repr__ method
def test_osl_repr():
    test_osl_r = OpenSourceLeg()
    assert test_osl_r.__repr__() == "OSL object. Frequency: 200 Hz"


# Test the OpenSourceLeg log_data method
def test_osl_log_data():
    test_osl_ld = OpenSourceLeg()
    assert test_osl_ld._log_data == False
    test_osl_ld.log_data()
    assert test_osl_ld._log_data == True


# Monkeypatch the get_active_ports method
@pytest.fixture
def mock_get_active_ports(monkeypatch):
    monkeypatch.setattr(
        "opensourceleg.utilities.get_active_ports", lambda: ["COM1", "COM2", "COM3"]
    )


# Monkeypatch the get_active_ports method
@pytest.fixture
def mock_get_active_ports1(monkeypatch):
    monkeypatch.setattr("opensourceleg.utilities.get_active_ports", lambda: ["COM1"])


# Monkeypatch the get_active_ports method
@pytest.fixture
def mock_get_active_ports0(monkeypatch):
    monkeypatch.setattr("opensourceleg.utilities.get_active_ports", lambda: [])


# Test the OpenSourceLeg add_joint method with no ports available
def test_osl_add_joint_no_ports(mock_get_active_ports0):
    # Create a new OpenSourceLeg
    test_osl_ajnp = OpenSourceLeg()
    test_osl_ajnp.log = Logger(file_path="tests/test_osl/test_osl_ajnp")
    test_osl_ajnp.log.set_stream_level("DEBUG")
    try:
        test_osl_ajnp.add_joint(name="knee")
    except SystemExit:
        with open("tests/test_osl/test_osl_ajnp.log", "r") as f:
            contents = f.read()
            assert (
                "WARNING: No active ports found, please ensure that the joint is connected and powered on."
                in contents
            )
    assert test_osl_ajnp._has_knee == False


# Test the OpenSourceLeg add_joint method with one port available
def test_osl_add_joint_one_port(joint_patched: Joint, mock_get_active_ports1):
    # Create a new OpenSourceLeg
    test_osl_ajop = OpenSourceLeg()
    test_osl_ajop.add_joint(name="knee")
    assert test_osl_ajop._has_knee == True
    assert test_osl_ajop._knee.name == "knee"
    assert test_osl_ajop._knee.port == "COM1"
    assert test_osl_ajop._knee.gear_ratio == 1.0
    assert test_osl_ajop._knee.max_temperature == 80
    assert test_osl_ajop._knee.is_homed == False
    assert test_osl_ajop._knee.encoder_map == None
    assert test_osl_ajop._knee.output_position == 0.0
    assert test_osl_ajop._knee.output_velocity == 0.0
    assert test_osl_ajop._knee.joint_torque == 0.0
    assert test_osl_ajop._knee.motor_current_sp == 0.0
    assert test_osl_ajop._knee.motor_voltage_sp == 0.0
    assert test_osl_ajop._knee.motor_position_sp == 0.0
    assert test_osl_ajop._knee.stiffness_sp == 200
    assert test_osl_ajop._knee.damping_sp == 400
    assert test_osl_ajop._knee.equilibirum_position_sp == 0.0
    assert test_osl_ajop._knee.control_mode_sp == "voltage"


# Test the OpenSourceLeg add_joint method
def test_osl_add_joint_ports_available(joint_patched: Joint, mock_get_active_ports):
    # Create a new OpenSourceLeg
    test_osl_aj = OpenSourceLeg()
    test_osl_aj.log = Logger(file_path="tests/test_osl/test_osl_aj")
    test_osl_aj.log.set_stream_level("DEBUG")
    test_osl_aj.add_joint(name="knee")
    assert test_osl_aj._has_knee == True
    assert test_osl_aj._knee.name == "knee"
    assert test_osl_aj._knee.port == "COM3"
    assert test_osl_aj._knee.gear_ratio == 1.0
    assert test_osl_aj._knee.max_temperature == 80
    assert test_osl_aj._knee.is_homed == False
    assert test_osl_aj._knee.encoder_map == None
    assert test_osl_aj._knee.output_position == 0.0
    assert test_osl_aj._knee.output_velocity == 0.0
    assert test_osl_aj._knee.joint_torque == 0.0
    assert test_osl_aj._knee.motor_current_sp == 0.0
    assert test_osl_aj._knee.motor_voltage_sp == 0.0
    assert test_osl_aj._knee.motor_position_sp == 0.0
    assert test_osl_aj._knee.stiffness_sp == 200
    assert test_osl_aj._knee.damping_sp == 400
    assert test_osl_aj._knee.equilibirum_position_sp == 0.0
    assert test_osl_aj._knee.control_mode_sp == "voltage"
    test_osl_aj.add_joint(name="ankle")
    assert test_osl_aj._has_ankle == True
    assert test_osl_aj._ankle.name == "ankle"
    assert test_osl_aj._ankle.port == "COM2"
    assert test_osl_aj._ankle.gear_ratio == 1.0
    assert test_osl_aj._ankle.max_temperature == 80
    assert test_osl_aj._ankle.is_homed == False
    assert test_osl_aj._ankle.encoder_map == None
    assert test_osl_aj._ankle.output_position == 0.0
    assert test_osl_aj._ankle.output_velocity == 0.0
    assert test_osl_aj._ankle.joint_torque == 0.0
    assert test_osl_aj._ankle.motor_current_sp == 0.0
    assert test_osl_aj._ankle.motor_voltage_sp == 0.0
    assert test_osl_aj._ankle.motor_position_sp == 0.0
    assert test_osl_aj._ankle.stiffness_sp == 200
    assert test_osl_aj._ankle.damping_sp == 400
    assert test_osl_aj._ankle.equilibirum_position_sp == 0.0
    assert test_osl_aj._ankle.control_mode_sp == "voltage"
    test_osl_aj.add_joint(name="loadcell")
    with open("tests/test_osl/test_osl_aj.log", "r") as f:
        contents = f.read()
        assert "[OSL] Joint name is not recognized." in contents


# Test the OpenSourceLeg add_loadcell method
def test_osl_add_loadcell(loadcell_patched: Loadcell):
    test_osl_al = OpenSourceLeg()
    test_osl_al.add_loadcell()
    assert test_osl_al._has_loadcell == True
    assert test_osl_al._loadcell._is_dephy == False
    assert test_osl_al._loadcell._joint == None
    assert test_osl_al._loadcell._amp_gain == 125.0
    assert test_osl_al._loadcell._exc == 5.0
    assert test_osl_al._loadcell._adc_range == 2**12 - 1
    assert test_osl_al._loadcell._offset == (2**12) / 2
    assert test_osl_al._loadcell._lc.bus == 1
    assert test_osl_al._loadcell._lc.addr == 0x66
    assert test_osl_al._loadcell._lc.indx == 0
    assert test_osl_al._loadcell._lc.is_streaming == True
    assert np.array_equal(
        test_osl_al._loadcell._loadcell_matrix, constants.LOADCELL_MATRIX
    )
    assert test_osl_al._loadcell._loadcell_data == None
    assert test_osl_al._loadcell._prev_loadcell_data == None
    assert np.array_equal(
        test_osl_al._loadcell._loadcell_zero, np.zeros(shape=(1, 6), dtype=np.double)
    )
    assert test_osl_al._loadcell._zeroed == False
    assert test_osl_al._loadcell._log == test_osl_al.log


# Test the OpenSourceLeg add_state_machine method
def test_osl_add_state_machine():
    test_osl_asm = OpenSourceLeg()
    test_osl_asm.add_state_machine()
    assert test_osl_asm._has_sm == True


# Override the exit() method
@pytest.fixture
def patch_exit(monkeypatch):
    monkeypatch.setattr("builtins.exit", lambda: None)


# Test the OpenSourceLeg update method with knee
def test_osl_update_knee(
    joint_patched: Joint, mock_get_active_ports, patch_sleep, patch_exit
):
    test_osl_u_knee = OpenSourceLeg()
    test_osl_u_knee.log = Logger(file_path="tests/test_osl/test_osl_u_knee")
    test_osl_u_knee.log.set_stream_level("DEBUG")
    test_osl_u_knee.add_joint(name="knee")
    test_osl_u_knee._knee._data = Data()
    test_osl_u_knee._knee.is_streaming = True
    test_osl_u_knee._knee._max_temperature = 1
    test_osl_u_knee.update()
    assert test_osl_u_knee._knee._data.batt_volt == 15
    with open("tests/test_osl/test_osl_u_knee.log", "r") as f:
        contents = f.read()
        assert "WARNING: [KNEE] Thermal limit 1.0 reached. Stopping motor." in contents


# Test the OpenSourceLeg update method with ankle
def test_osl_update_ankle(
    joint_patched: Joint, mock_get_active_ports, patch_sleep, patch_exit
):
    test_osl_u_ankle = OpenSourceLeg()
    test_osl_u_ankle.log = Logger(file_path="tests/test_osl/test_osl_u_ankle")
    test_osl_u_ankle.log.set_stream_level("DEBUG")
    test_osl_u_ankle.add_joint(name="ankle")
    test_osl_u_ankle._ankle._data = Data()
    test_osl_u_ankle._ankle.is_streaming = True
    test_osl_u_ankle._ankle._max_temperature = 1
    test_osl_u_ankle.update()
    assert test_osl_u_ankle._ankle._data.batt_volt == 15
    with open("tests/test_osl/test_osl_u_ankle.log", "r") as f:
        contents = f.read()
        assert "WARNING: [ANKLE] Thermal limit 1.0 reached. Stopping motor." in contents


# Test the OpenSourceLeg update method with loadcell
def test_osl_update_loadcell(loadcell_patched: Loadcell, patch_sleep):
    test_osl_u_loadcell = OpenSourceLeg()
    test_osl_u_loadcell.log = Logger(file_path="tests/test_osl/test_osl_u_loadcell")
    test_osl_u_loadcell.log.set_stream_level("DEBUG")
    test_osl_u_loadcell.add_loadcell()
    test_osl_u_loadcell._loadcell._joint = joint_patched
    test_osl_u_loadcell._loadcell._joint._data = Data(
        genvar_0=1, genvar_1=2, genvar_2=3, genvar_3=4, genvar_4=5, genvar_5=6
    )
    test_osl_u_loadcell.update()
    loadcell_coupled = [
        ((1 - (2**12) / 2) / (2**12 - 1) * 5.0) * 1000 / (5.0 * 125.0),
        ((2 - (2**12) / 2) / (2**12 - 1) * 5.0) * 1000 / (5.0 * 125.0),
        ((3 - (2**12) / 2) / (2**12 - 1) * 5.0) * 1000 / (5.0 * 125.0),
        ((4 - (2**12) / 2) / (2**12 - 1) * 5.0) * 1000 / (5.0 * 125.0),
        ((5 - (2**12) / 2) / (2**12 - 1) * 5.0) * 1000 / (5.0 * 125.0),
        ((6 - (2**12) / 2) / (2**12 - 1) * 5.0) * 1000 / (5.0 * 125.0),
    ]
    loadcell_signed = [
        [
            loadcell_coupled[0] * -38.72600,
            loadcell_coupled[0] * -1817.74700,
            loadcell_coupled[0] * 9.84900,
            loadcell_coupled[0] * 43.37400,
            loadcell_coupled[0] * -44.54000,
            loadcell_coupled[0] * 1824.67000,
        ],
        [
            loadcell_coupled[1] * -8.61600,
            loadcell_coupled[1] * 1041.14900,
            loadcell_coupled[1] * 18.86100,
            loadcell_coupled[1] * -2098.82200,
            loadcell_coupled[1] * 31.79400,
            loadcell_coupled[1] * 1058.6230,
        ],
        [
            loadcell_coupled[2] * -1047.16800,
            loadcell_coupled[2] * 8.63900,
            loadcell_coupled[2] * -1047.28200,
            loadcell_coupled[2] * -20.70000,
            loadcell_coupled[2] * -1073.08800,
            loadcell_coupled[2] * -8.92300,
        ],
        [
            loadcell_coupled[3] * 20.57600,
            loadcell_coupled[3] * -0.04000,
            loadcell_coupled[3] * -0.24600,
            loadcell_coupled[3] * 0.55400,
            loadcell_coupled[3] * -21.40800,
            loadcell_coupled[3] * -0.47600,
        ],
        [
            loadcell_coupled[4] * -12.13400,
            loadcell_coupled[4] * -1.10800,
            loadcell_coupled[4] * 24.36100,
            loadcell_coupled[4] * 0.02300,
            loadcell_coupled[4] * -12.14100,
            loadcell_coupled[4] * 0.79200,
        ],
        [
            loadcell_coupled[5] * -0.65100,
            loadcell_coupled[5] * -28.28700,
            loadcell_coupled[5] * 0.02200,
            loadcell_coupled[5] * -25.23000,
            loadcell_coupled[5] * 0.47300,
            loadcell_coupled[5] * -27.3070,
        ],
    ]
    loadcell_signed_added_and_transposed = [
        [
            loadcell_signed[0][0]
            + loadcell_signed[0][1]
            + loadcell_signed[0][2]
            + loadcell_signed[0][3]
            + loadcell_signed[0][4]
            + loadcell_signed[0][5],
            loadcell_signed[1][0]
            + loadcell_signed[1][1]
            + loadcell_signed[1][2]
            + loadcell_signed[1][3]
            + loadcell_signed[1][4]
            + loadcell_signed[1][5],
            loadcell_signed[2][0]
            + loadcell_signed[2][1]
            + loadcell_signed[2][2]
            + loadcell_signed[2][3]
            + loadcell_signed[2][4]
            + loadcell_signed[2][5],
            loadcell_signed[3][0]
            + loadcell_signed[3][1]
            + loadcell_signed[3][2]
            + loadcell_signed[3][3]
            + loadcell_signed[3][4]
            + loadcell_signed[3][5],
            loadcell_signed[4][0]
            + loadcell_signed[4][1]
            + loadcell_signed[4][2]
            + loadcell_signed[4][3]
            + loadcell_signed[4][4]
            + loadcell_signed[4][5],
            loadcell_signed[5][0]
            + loadcell_signed[5][1]
            + loadcell_signed[5][2]
            + loadcell_signed[5][3]
            + loadcell_signed[5][4]
            + loadcell_signed[5][5],
        ],
        [0, 0, 0, 0, 0, 0],
    ]
    # Assert the proper values are returned with a couple significant figures
    assert round(test_osl_u_loadcell._loadcell.fx, -2) == round(
        loadcell_signed_added_and_transposed[0][0], -2
    )
    assert round(test_osl_u_loadcell._loadcell.fy) == round(
        loadcell_signed_added_and_transposed[0][1]
    )
    assert round(test_osl_u_loadcell._loadcell.fz, -3) == round(
        loadcell_signed_added_and_transposed[0][2], -3
    )
    assert round(test_osl_u_loadcell._loadcell.mx) == round(
        loadcell_signed_added_and_transposed[0][3]
    )
    assert round(test_osl_u_loadcell._loadcell.my) == round(
        loadcell_signed_added_and_transposed[0][4]
    )
    assert round(test_osl_u_loadcell._loadcell.mz, -1) == round(
        loadcell_signed_added_and_transposed[0][5], -1
    )


# Test the OpenSourceLeg update method with _log_data
def test_osl_update_log_data(joint_patched: Joint, mock_get_active_ports, patch_sleep):
    test_osl_u_ld = OpenSourceLeg()
    test_osl_u_ld.log = Logger(file_path="tests/test_osl/test_osl_u_ld")
    test_osl_u_ld.log.set_stream_level("DEBUG")
    test_osl_u_ld.add_joint(name="knee")
    test_osl_u_ld._log_data = True
    test_osl_u_ld._knee._data = Data()
    test_osl_u_ld._knee.is_streaming = True
    assert test_osl_u_ld._log_data == True
    test_class_instance = Simple_Class()
    test_osl_u_ld.log.add_attributes(
        class_instance=test_class_instance, attributes_str=["a", "b", "c"]
    )
    test_osl_u_ld.update()
    expected_rows = [["a", "b", "c"], ["1", "2", "3"]]
    with open("tests/test_osl/test_osl_u_ld.csv", "r", newline="") as f:
        reader = csv.reader(f)
        rows = list(reader)
        assert rows == expected_rows


# Test the OpenSourceLeg update method with state machine
def test_osl_update_state_machine(
    joint_patched: Joint, mock_get_active_ports, patch_sleep, patch_exit
):
    test_osl_u_sm = OpenSourceLeg()
    test_osl_u_sm.log = Logger(file_path="tests/test_osl/test_osl_u_sm")
    test_osl_u_sm.log.set_stream_level("DEBUG")
    test_osl_u_sm.add_joint(name="knee")
    test_osl_u_sm._knee._data = Data()
    test_osl_u_sm._knee.is_streaming = True
    test_osl_u_sm._knee._max_temperature = 10000
    test_osl_u_sm.add_state_machine()
    assert test_osl_u_sm.has_state_machine == True
    test_osl_u_sm.home()
    assert test_osl_u_sm.is_sm_running == False
    test_osl_u_sm.state_machine._initial_state = State(name="state_1")
    test_osl_u_sm.state_machine._current_state = None
    test_osl_u_sm.update()
    assert test_osl_u_sm.state_machine._current_state.name == "state_1"
    assert test_osl_u_sm.is_sm_running == True
    test_osl_u_sm.state_machine._exited = False
    test_osl_u_sm.state_machine._osl = OpenSourceLeg()
    test_osl_u_sm.state_machine.add_state(state=State(name="state_1"))
    test_osl_u_sm.state_machine.add_state(state=State(name="state_2"))
    test_osl_u_sm.state_machine.add_event(event=Event(name="test_event_1"))
    transition1 = test_osl_u_sm.state_machine.add_transition(
        source=State(name="state_1"),
        destination=State(name="state_2"),
        event=Event(name="test_event_1"),
    )
    assert test_osl_u_sm.state_machine._transitions == [transition1]
    test_osl_u_sm.update()
    assert test_osl_u_sm.state_machine._current_state.name == "state_2"
    test_osl_u_sm.state_machine._current_state.make_knee_active()
    assert test_osl_u_sm._knee._mode == VoltageMode(device=test_osl_u_sm._knee)
    transition2 = test_osl_u_sm.state_machine.add_transition(
        source=State(name="state_2"),
        destination=State(name="state_1"),
        event=Event(name="test_event_2"),
    )
    test_osl_u_sm.update(set_state_machine_parameters=True)
    assert test_osl_u_sm._knee._mode == ImpedanceMode(device=test_osl_u_sm._knee)
    assert test_osl_u_sm._knee._gains == {
        "kp": 40,
        "ki": 400,
        "kd": 0,
        "k": 0,
        "b": 0,
        "ff": 128,
    }
    assert test_osl_u_sm._knee._motor_command == "Control Mode: c_int(3), Value: 5010"


def test_osl_update_state_machine_ankle(
    joint_patched: Joint, mock_get_active_ports, patch_sleep, patch_exit
):
    test_osl_u_sm_ank = OpenSourceLeg()
    test_osl_u_sm_ank.log = Logger(file_path="tests/test_osl/test_osl_u_sm_ank")
    test_osl_u_sm_ank.log.set_stream_level("DEBUG")
    test_osl_u_sm_ank.add_joint(name="ankle")
    test_osl_u_sm_ank._ankle._data = Data()
    test_osl_u_sm_ank._ankle.is_streaming = True
    test_osl_u_sm_ank._ankle._max_temperature = 10000
    test_osl_u_sm_ank.add_state_machine()
    assert test_osl_u_sm_ank.has_state_machine == True
    test_osl_u_sm_ank.home()
    assert test_osl_u_sm_ank.is_sm_running == False
    test_osl_u_sm_ank.state_machine._initial_state = State(name="state_1")
    test_osl_u_sm_ank.state_machine._current_state = None
    test_osl_u_sm_ank.update()
    assert test_osl_u_sm_ank.state_machine._current_state.name == "state_1"
    assert test_osl_u_sm_ank.is_sm_running == True
    test_osl_u_sm_ank.state_machine._exited = False
    test_osl_u_sm_ank.state_machine._osl = OpenSourceLeg()
    test_osl_u_sm_ank.state_machine.add_state(state=State(name="state_1"))
    test_osl_u_sm_ank.state_machine.add_state(state=State(name="state_2"))
    test_osl_u_sm_ank.state_machine.add_event(event=Event(name="test_event_1"))
    transition1 = test_osl_u_sm_ank.state_machine.add_transition(
        source=State(name="state_1"),
        destination=State(name="state_2"),
        event=Event(name="test_event_1"),
    )
    assert test_osl_u_sm_ank.state_machine._transitions == [transition1]
    test_osl_u_sm_ank.update()
    assert test_osl_u_sm_ank.state_machine._current_state.name == "state_2"
    test_osl_u_sm_ank.state_machine._current_state.make_ankle_active()
    assert test_osl_u_sm_ank._ankle._mode == VoltageMode(
        device=test_osl_u_sm_ank._ankle
    )
    transition2 = test_osl_u_sm_ank.state_machine.add_transition(
        source=State(name="state_2"),
        destination=State(name="state_1"),
        event=Event(name="test_event_2"),
    )
    test_osl_u_sm_ank.update(set_state_machine_parameters=True)
    assert test_osl_u_sm_ank._ankle._mode == ImpedanceMode(
        device=test_osl_u_sm_ank._ankle
    )
    assert test_osl_u_sm_ank._ankle._gains == {
        "kp": 40,
        "ki": 400,
        "kd": 0,
        "k": 0,
        "b": 0,
        "ff": 128,
    }
    assert (
        test_osl_u_sm_ank._ankle._motor_command == "Control Mode: c_int(3), Value: 6375"
    )


def test_osl_run(joint_patched: Joint, mock_get_active_ports, patch_sleep, patch_exit):
    test_osl_r = OpenSourceLeg()
    test_osl_r.log = Logger(file_path="tests/test_osl/test_osl_r")
    test_osl_r.log.set_stream_level("DEBUG")
    test_osl_r.add_joint(name="knee")
    test_osl_r._knee._data = Data()
    test_osl_r._knee.is_streaming = True
    test_osl_r._knee._max_temperature = 10000
    test_osl_r.add_state_machine()
    test_osl_r.home()
    assert test_osl_r.is_sm_running == False
    test_osl_r.state_machine._initial_state = State(name="state_1")
    test_osl_r.state_machine._current_state = None
    assert test_osl_r._log_data == False
    test_osl_r.run(log_data=True)
    assert test_osl_r.is_sm_running == True
    assert test_osl_r._log_data == True


# Test the OpenSourceLeg estop method
def test_osl_estop():
    test_osl_es = OpenSourceLeg()
    test_osl_es.log = Logger(file_path="tests/test_osl/test_osl_es")
    test_osl_es.log.set_stream_level("DEBUG")
    test_osl_es.estop()
    with open("tests/test_osl/test_osl_es.log", "r") as f:
        contents = f.read()
        assert "[OSL] Emergency stop activated." in contents


# Unfinished: Assert the home methods were called
# Test the OpenSourceLeg home method
def test_osl_home(joint_patched: Joint, mock_get_active_ports):
    test_osl_h = OpenSourceLeg()
    test_osl_h.add_joint(name="knee")
    test_osl_h.add_joint(name="ankle")
    test_osl_h._knee._data = Data(mot_ang=20, ank_ang=10)
    test_osl_h.log = Logger(file_path="tests/test_osl/test_osl_h")
    test_osl_h.log.set_stream_level("DEBUG")
    test_osl_h.home()
    with open("tests/test_osl/test_osl_h.log", "r") as f:
        contents = f.read()
        assert "[OSL] Homing knee joint." in contents
        assert "[OSL] Homing ankle joint." in contents
    assert test_osl_h._knee._is_homed == True


# Test the OpenSourceLeg calibrate_loadcell method
def test_osl_calibrate_loadcell(loadcell_patched: Loadcell):
    test_osl_cl = OpenSourceLeg()
    test_osl_cl.add_loadcell()
    test_osl_cl._loadcell._zeroed = True
    test_osl_cl.log = Logger(file_path="tests/test_osl/test_osl_cl")
    test_osl_cl.log.set_stream_level("DEBUG")
    test_osl_cl.calibrate_loadcell()
    with open("tests/test_osl/test_osl_cl.log", "r") as f:
        contents = f.read()
        assert "[OSL] Calibrating loadcell." in contents
    assert test_osl_cl._loadcell._zeroed == False


# Test the OpenSourceLeg calibrate_encoders method
def test_osl_calibrate_encoders(
    joint_patched: Joint, mock_get_active_ports, patch_time_time, patch_sleep
):
    test_osl_ce = OpenSourceLeg()
    test_osl_ce.log = Logger(file_path="tests/test_osl/test_osl_ce")
    test_osl_ce.log.set_stream_level("DEBUG")
    test_osl_ce.add_joint(name="knee")
    test_osl_ce._knee._data = Data(mot_cur=4999)
    test_osl_ce._knee.is_streaming = True
    test_osl_ce._knee.home()
    test_osl_ce.calibrate_encoders()
    with open("tests/test_osl/test_osl_ce.log", "r") as f:
        contents = f.read()
        assert "[OSL] Calibrating encoders." in contents
    test_joint_position_array = [0.005752427954571154, 0.011504855909142308]
    test_output_position_array = [0.00013861305580425867, 0.00027722611160851734]
    test_power = np.arange(4.0)
    test_a_mat = np.array(test_joint_position_array).reshape(-1, 1) ** test_power
    test_beta = np.linalg.lstsq(test_a_mat, test_output_position_array, rcond=None)[0]
    test_coeffs = test_beta[0]
    test_encoder_map = np.polynomial.polynomial.Polynomial(coef=test_coeffs)
    # assert test_osl_ce._knee._encoder_map == test_encoder_map


# Test the OpenSourceLeg reset method
def test_osl_reset(joint_patched: Joint, mock_get_active_ports, patch_sleep):
    test_osl_r = OpenSourceLeg()
    test_osl_r.add_joint(name="knee")
    test_osl_r.add_joint(name="ankle")
    test_osl_r._knee._mode = CurrentMode(device=test_osl_r._knee)
    test_osl_r._ankle._mode = ImpedanceMode(device=test_osl_r._ankle)
    test_osl_r.reset()
    assert test_osl_r._knee._mode == VoltageMode(device=test_osl_r._knee)
    assert test_osl_r._ankle._mode == VoltageMode(device=test_osl_r._ankle)
    assert test_osl_r._knee._motor_command == "Control Mode: c_int(1), Value: 0"
    assert test_osl_r._ankle._motor_command == "Control Mode: c_int(1), Value: 0"


# Test the OpenSourceLeg default properties
def test_osl_properties(mock_time):
    test_osl_prop = OpenSourceLeg()
    test_osl_prop.log = Logger(file_path="tests/test_osl/test_osl_prop")
    assert test_osl_prop.timestamp == 1.0
    knee_prop = test_osl_prop.knee
    assert knee_prop == None
    with open("tests/test_osl/test_osl_prop.log", "r") as f:
        contents = f.read()
        assert "WARNING: [OSL] Knee is not connected." in contents
    ankle_prop = test_osl_prop.ankle
    assert ankle_prop == None
    with open("tests/test_osl/test_osl_prop.log", "r") as f:
        contents = f.read()
        assert "WARNING: [OSL] Ankle is not connected." in contents
    loadcell_prop = test_osl_prop.loadcell
    assert loadcell_prop == None
    with open("tests/test_osl/test_osl_prop.log", "r") as f:
        contents = f.read()
        assert "WARNING: [OSL] Loadcell is not connected." in contents
    assert test_osl_prop.units == DEFAULT_UNITS
    assert test_osl_prop.has_knee == False
    assert test_osl_prop.has_ankle == False
    assert test_osl_prop.has_loadcell == False
    assert test_osl_prop.has_state_machine == False
    assert test_osl_prop.has_tui == False
    assert test_osl_prop.is_homed == False
    assert test_osl_prop.is_sm_running == False
