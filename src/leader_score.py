import numpy as np


def compute_leader_score(
    rs,
    rotation_score,
    rs_sector,
    inst,
    inst_flow,
    mf,
    flow_timeline,
    voe
):

    # =========================
    # SECTOR SCORE
    # =========================
    sector_score = np.tanh(rotation_score / 2)

    # =========================
    # RS VS SECTOR
    # =========================
    rs_sector_score = np.tanh(rs_sector * 5)

    # =========================
    # SMART MONEY
    # =========================
    sm = (
        inst * 1.2 +
        inst_flow * 1.5 +
        mf * 1.3
    )

    sm_score = np.tanh(sm)

    # =========================
    # TIMING
    # =========================
    timing = (
        flow_timeline * 1.2 +
        voe * 1.0
    )

    timing_score = np.tanh(timing)

    # =========================
    # FINAL SCORE
    # =========================
    score = (
        rs * 2.0 +
        sector_score * 1.5 +
        rs_sector_score * 1.5 +
        sm_score * 1.8 +
        timing_score * 1.2
    )

    return float(np.tanh(score) * 3)
