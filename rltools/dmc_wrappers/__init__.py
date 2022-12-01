"""dm_control env wrappers."""
from rltools.dmc_wrappers.action_repeat import ActionRepeat
from rltools.dmc_wrappers.action_rescale import ActionRescale
from rltools.dmc_wrappers.discretize import DiscreteActionWrapper
from rltools.dmc_wrappers.frames_stack import FrameStack
from rltools.dmc_wrappers.obs_filter import ObsFilter
from rltools.dmc_wrappers.pixels import PixelsWrapper
from rltools.dmc_wrappers.point_clouds import PointCloudWrapper
from rltools.dmc_wrappers.states import StatesWrapper
from rltools.dmc_wrappers.types_cast import TypesCast

try:
    from rltools.dmc_wrappers.gym_adapter import DmcToGym, GymToDmc
except ImportError:
    import logging
    logging.info("Skipping gym")

from rltools.dmc_wrappers.base import EnvironmentSpecs
