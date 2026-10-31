"""
IEEE 14-bus: Load Flow + Short Circuit Study
Run:  python ieee14_study.py
Outputs go to the folder ./results
"""
import os
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import pandapower as pp
import pandapower.networks as nw
import pandapower.shortcircuit as sc

os.makedirs("results", exist_ok=True)

# ------------------------------------------------------------
# 1. LOAD FLOW
# ------------------------------------------------------------
net = nw.case14()
pp.runpp(net, algorithm="nr", init="dc")

# Bus results
bus = net.res_bus.copy()
bus.insert(0, "bus", net.bus.index)
bus["vm_pu"] = bus["vm_pu"].round(4)
bus["va_degree"] = bus["va_degree"].round(2)
bus["p_mw"] = bus["p_mw"].round(2)
bus["q_mvar"] = bus["q_mvar"].round(2)
bus["voltage_ok"] = bus["vm_pu"].between(0.95, 1.05)   # +-5% limit
bus.to_csv("results/load_flow_buses.csv", index=False)

# Line and transformer loading
lines = net.res_line[["p_from_mw", "q_from_mvar", "p_to_mw", "pl_mw",
                      "loading_percent"]].round(2)
lines.insert(0, "from_bus", net.line.from_bus)
lines.insert(1, "to_bus", net.line.to_bus)
lines.to_csv("results/load_flow_lines.csv", index=False)

trafos = net.res_trafo[["p_hv_mw", "q_hv_mvar", "pl_mw",
                        "loading_percent"]].round(2)
trafos.to_csv("results/load_flow_trafos.csv")

# System summary
p_gen = net.res_gen.p_mw.sum() + net.res_ext_grid.p_mw.sum()
p_load = net.res_load.p_mw.sum()
losses = net.res_line.pl_mw.sum() + net.res_trafo.pl_mw.sum()
summary = {
    "Total generation (MW)": round(p_gen, 2),
    "Total load (MW)": round(p_load, 2),
    "Total losses (MW)": round(losses, 2),
    "Min voltage (pu)": round(net.res_bus.vm_pu.min(), 4),
    "Max voltage (pu)": round(net.res_bus.vm_pu.max(), 4),
    "Max line loading (%)": round(net.res_line.loading_percent.max(), 2),
}
pd.Series(summary).to_csv("results/load_flow_summary.csv", header=["value"])

# Voltage profile plot
plt.figure(figsize=(8, 4))
plt.bar(net.bus.index, net.res_bus.vm_pu, color="steelblue")
plt.axhline(1.05, color="red", ls="--", label="Upper limit 1.05")
plt.axhline(0.95, color="red", ls="--", label="Lower limit 0.95")
plt.ylim(0.9, 1.1)
plt.xlabel("Bus")
plt.ylabel("Voltage (pu)")
plt.title("IEEE 14-bus voltage profile")
plt.legend()
plt.tight_layout()
plt.savefig("results/voltage_profile.png", dpi=150)
plt.close()

# ------------------------------------------------------------
# 2. SHORT CIRCUIT (IEC 60909, three-phase fault)
# ------------------------------------------------------------
# The standard case14 has no short circuit data, so we ASSUME values.
# State these assumptions clearly in your report.
net.ext_grid["s_sc_max_mva"] = 5000.0
net.ext_grid["s_sc_min_mva"] = 3000.0
net.ext_grid["rx_max"] = 0.1
net.ext_grid["rx_min"] = 0.1

net.gen["vn_kv"] = net.bus.loc[net.gen.bus.values, "vn_kv"].values
net.gen["sn_mva"] = 100.0
net.gen["xdss_pu"] = 0.2
net.gen["rdss_ohm"] = 0.0
net.gen["cos_phi"] = 0.85

sc.calc_sc(net, case="max", fault="3ph", ip=False, ith=False)
sc_max = net.res_bus_sc[["ikss_ka"]].copy()
sc_max.insert(0, "bus", net.bus.index)
sc_max["vn_kv"] = net.bus.vn_kv.values
sc_max["ikss_ka"] = sc_max["ikss_ka"].round(3)
sc_max["sk_mva"] = (np.sqrt(3) * sc_max["vn_kv"] * sc_max["ikss_ka"]).round(1)
sc_max.to_csv("results/short_circuit_max_3ph.csv", index=False)

plt.figure(figsize=(8, 4))
plt.bar(sc_max["bus"], sc_max["ikss_ka"], color="darkorange")
plt.xlabel("Bus")
plt.ylabel("Initial short-circuit current Ik'' (kA)")
plt.title("Maximum 3-phase fault current per bus")
plt.tight_layout()
plt.savefig("results/short_circuit_currents.png", dpi=150)
plt.close()

# ------------------------------------------------------------
# 3. PRINT KEY RESULTS
# ------------------------------------------------------------
print("\n=== LOAD FLOW SUMMARY ===")
for k, v in summary.items():
    print(f"{k}: {v}")
print("\nBuses outside 0.95-1.05 pu:",
      list(bus.loc[~bus.voltage_ok, "bus"]) or "none")
print("\n=== SHORT CIRCUIT (max, 3-phase) ===")
print(sc_max.to_string(index=False))
print("\nFiles saved in ./results")
