"""Apply per-cylinder runner-entry geometry to the existing V2 loft and centerline."""


def attach(generator):
    build = generator.build_single_runner_components
    curve = generator.runner_bezier_points

    def runner_params(x_center, params):
        runners = params["runners"]
        index = runners["center_x_mm"].index(x_center)
        overrides = runners.get("entry_sweep_overrides", {}).get(str(index + 1))
        if overrides is None:
            return params
        return {**params, "runners": {**runners, "sweep": {**runners["sweep"], **overrides}}}

    def build_runner(x_center, params):
        return build(x_center, runner_params(x_center, params))

    def runner_curve(x_center, params):
        return curve(x_center, runner_params(x_center, params))

    generator.build_single_runner_components = build_runner
    generator.runner_bezier_points = runner_curve
