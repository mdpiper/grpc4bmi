from pathlib import Path
from textwrap import dedent
import numpy as np
from numpy.testing import assert_array_equal
import pytest


try:
    from grpc4bmi.bmi_julia_model import BmiJulia,install
    from juliacall import Main as jl
except ImportError:
    BmiJulia = None

@pytest.mark.skipif(not BmiJulia, reason="Julia and its dependencies are not installed")
class TestJuliaHeatModel:
    @pytest.fixture(scope="class", autouse=True)
    def install_heat(self):
        # TODO for other Julia models do we need to install BasicModelInterface?
        # it is dep of Heat.jl, but we use it directly
        install('BasicModelInterface')
        jl.Pkg.add(
            url="https://github.com/csdms/bmi-example-julia.git",
            rev="d8b354ceddf6b048727c2e214031f43d62964120",
        )
       

    @pytest.fixture
    def cfg_file(self, tmp_path: Path):
        fn = tmp_path / "heat.toml"
        fn.write_text(
            dedent(
                """\
                # Heat model configuration
                shape = [6, 8]
                spacing = [1.0, 1.0]
                origin = [0.0, 0.0]
                alpha = 1.0
                """
            )
        )
        return fn

    @pytest.fixture
    def model(self, cfg_file):
        model = BmiJulia.from_name("Heat.Model")
        model.initialize(str(cfg_file))
        return model

    @pytest.mark.parametrize(
        "fn_name,fn_args,expected",
        [
            ("get_component_name", tuple(), "The 2D Heat Equation"),
            ("get_input_item_count", tuple(), 1),
            ("get_output_item_count", tuple(), 1),
            ("get_input_var_names", tuple(), ["plate_surface__temperature"]),
            ("get_output_var_names", tuple(), ["plate_surface__temperature"]),
            ("get_start_time", tuple(), 0.0),
            ("get_end_time", tuple(), np.Inf),
            ("get_time_step", tuple(), 0.25),
            ("get_time_units", tuple(), "s"),
            ("get_var_type", ["plate_surface__temperature"], "float64"),
            ("get_var_units", ["plate_surface__temperature"], "K"),
            ("get_var_itemsize", ["plate_surface__temperature"], 8),
            ("get_var_nbytes", ["plate_surface__temperature"], 384),
            ("get_var_grid", ["plate_surface__temperature"], 0),
            ("get_var_location", ["plate_surface__temperature"], "node"),
            # result of get_grid_shape is incompatible with spec, 
            # as it says order should be y,x not x,y
            ("get_grid_shape", [0, np.zeros((2,))], [6, 8]),
            ("get_grid_spacing", [0, np.zeros((2,))], [1.0, 1.0]),
            ("get_grid_origin", [0, np.zeros((2,))], [0.0, 0.0]),
            ("get_grid_rank", [0], 2),
            ("get_grid_size", [0], 48),
            ("get_grid_type", [0], "uniform_rectilinear"),
            ("get_grid_node_count", [0], 48),
            ("update", tuple(), None),
            ("update_until", [2], None),
            ("finalize", tuple(), None),
            ("get_current_time", tuple(), 0.0),
        ],
    )
    def test_methods(self, model: BmiJulia, fn_name, fn_args, expected):
        fn = getattr(model, fn_name)
        if fn_args == tuple():
            result = fn()
        else:
            result = fn(*fn_args)

        try:
            assert_array_equal(result, expected)
        except:
            assert result == expected

    def test_get_value(self, model: BmiJulia):
        result = model.get_value("plate_surface__temperature", np.zeros((48,)))
        assert result.shape == (48,)
        assert result.dtype == np.float64
        # cannot test values as model is initialized with random values

    def test_get_value_ptr(self, model: BmiJulia):
        with pytest.raises(NotImplementedError):
            model.get_value_ptr("plate_surface__temperature")

    # TODO fix gives no method matching error
    # def test_get_value_at_indices(self, model: BmiJulia):
    #     result = model.get_value_at_indices(
    #         "plate_surface__temperature", np.zeros((3,)), np.array([5, 6, 7])
    #     )
    #     assert result.shape == (3,)
    #     assert result.dtype == np.float64
        # cannot test values as model is initialized with random values

    # TODO fix gives DimensionMismatch error now
    # def test_set_value(self, model: BmiJulia):
    #     model.set_value("plate_surface__temperature", np.ones((48,)))

    #     result = model.get_value("plate_surface__temperature", np.zeros((48,)))
    #     assert_array_equal(result, np.ones((48,)))

    # TODO test set_value_at_indices method

# TODO Heat.jl does not implement all methods, use fake.jl to test all methods not covered by Heat.jl
"""
To test

get_grid_x
get_grid_y
get_grid_z
get_grid_edge_count
get_grid_face_count
get_grid_edge_nodes
get_grid_face_edges
get_grid_face_nodes
get_grid_nodes_per_face
"""
@pytest.mark.skipif(not BmiJulia, reason="Julia and its dependencies are not installed")
class TestJuliaFakeModel:
    @pytest.fixture(scope="class", autouse=True)
    def install_fake(self):
        install('BasicModelInterface')

    @pytest.fixture
    def model(self, cfg_file):
        jl.seval('include("fake.jl")')
        model = BmiJulia.from_name(".FakeModel.Model", ".FakeModel.BMI")
        model.initialize(str(cfg_file))
        return model
    
    @pytest.mark.parametrize(
        "fn_name,fn_args,expected",
        [
            ("get_grid_x", [0, np.zeros((2,))], [1, 2]),
        ],
    )
    def test_methods(self, model: BmiJulia, fn_name, fn_args, expected):
        fn = getattr(model, fn_name)
        if fn_args == tuple():
            result = fn()
        else:
            result = fn(*fn_args)

        try:
            assert_array_equal(result, expected)
        except:
            assert result == expected