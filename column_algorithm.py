from .Test_Column_ObjFnc import tac_column
import time


def distColumn_model(x, Problem):
    # Independent Variables
    CR = x[0]  # * RR: Reflux Ratio
    P = x[1]  # * P: Condenser Pressure

    NR = x[2]  # * NR: Number of active trays in rectifying section
    NS = x[3]  # * NS: Number of active trays in stripping  section
    ND = x[4]  # * ND: Number of active trays in drawing section
    FT = x[5]  # Feed Temperature


    HyObject = Problem.HyObject  # Recover Hysys Objects from structure Problem
    NT = (NR + NS + ND) + 1  # Total number of active trays
    Feed_S = NR + ND + 1  # Feed location

    # 01 Change Column Topology and Column specifications (degrees of freedom)
    HyObject = Problem.HyObject  # Recover Hysys Objects from structure Problem

    ##Tower pressure
    HyObject.HySolver.CanSolve = False  ## Pause the hysys solver to avoid generating error
    DeltaP = (0.6895 * NT + 20)
    HyObject.MaterialStream.Bottoms.Pressure.SetValue(P + DeltaP, "kPa")
    HyObject.MaterialStream.Distillate.Pressure.SetValue(P, "kPa")
    HyObject.HySolver.CanSolve = True  ## Resume Solver

    # Total number of active trays
    HyObject.DistColumn.Main_TS.NumberOfTrays = NT

    # Feed location
    HyObject.DistColumn.Main_TS.SpecifyFeedLocation(HyObject.DistColumn.FeedMainTS, Feed_S)
    HyObject.DistColumn.Main_TS.SpecifyDrawLocation(HyObject.DistColumn.DrawMainTS, ND + 1)

    # Reflux Ratio
    HyObject.DistColumn.Column.ColumnFlowsheet.Specifications.Item('Comp Recovery').GoalValue = CR

    # Feed Temperature
    HyObject.MaterialStream.Feed.Temperature.SetValue(FT, 'C')

    # Boilup Ratio
    # HyObject.DistColumn.Column.ColumnFlowsheet.Specifications.Item('Boilup Ratio').GoalValue = BR
    ##-------------------------------------------------------------------------------------------------##

    # 02 Run Aspen Hysys model with new topology
    HyObject.DistColumn.ColumnFlowsheet.Run()  # Run Aspen Hysy model
    time.sleep(0.1)

    # 03 Check model convergence
    RunStatus = HyObject.HyApp.ActiveDocument.Flowsheet.Operations.Item(0).ColumnFlowsheet.CfsConverged

    if RunStatus == 1:

        # 04 Compute the Total Annual Cost of the Distillation Column
        ColumnCost = tac_column(Problem)  # from Test_Column_ObjFnc

        # 05 Check purity constraints
        PG_purity = 0.95
        Comp_frac_PG_Bott = HyObject.MaterialStream.Bottoms.ComponentMolarFractionValue[2]

        w1 = 0

        if Comp_frac_PG_Bott < PG_purity:
            w1 = (PG_purity - Comp_frac_PG_Bott) * 1e10

        # Total Annual Cost + penalty terms

        TAC = ColumnCost.TAC + w1
    else:  # In case model does not converge

        TAC = 1e5
    return (TAC)
