#!/usr/bin/env python3
"""Prepare resource-only integration probes. No production source edits."""
from pathlib import Path
import shutil
ROOT=Path(__file__).resolve().parents[3]
EXP=Path(__file__).resolve().parent
BUILD=ROOT/'rtl/build/ip_evaluation_resources'
BUILD.mkdir(parents=True,exist_ok=True)
ip_candidates=[ROOT/'rtl/build/fft_ip_trial/lite_bram/fft32_ip.ngc',Path('/tmp/ax309-fft-ip-20261112/lite_bram/fft32_ip.ngc')]
ip=next((p for p in ip_candidates if p.is_file()),None)
if ip is None:raise RuntimeError('Generate the Lite-BRAM FFT v7.1 benchmark first')
store=BUILD/'ip';store.mkdir(exist_ok=True);shutil.copy2(ip,store/'fft32_ip.ngc')
uart=(ROOT/'rtl/uart/uart_s05_session_top.v').read_text()
uart=uart.replace('module uart_s05_session_top #(','module uart_s05_shared_resource_probe #(')
uart=uart.replace('    output wire tx_retry_exhausted\n','    output wire tx_retry_exhausted,\n    input wire dsp_mem_active,\n    input wire [12:0] dsp_read_addr,\n    output wire [31:0] dsp_read_word\n')
uart=uart.replace('    s05_iq_cpi_banked u_iq_store (','    assign dsp_read_word=iq_read_word;\n    s05_iq_cpi_banked u_iq_store (')
uart=uart.replace('.read_addr(iq_read_addr),','.read_addr(dsp_mem_active?dsp_read_addr:iq_read_addr),')
(BUILD/'uart_shared_probe.v').write_text(uart)
stub=(ROOT/'rtl/experiments/fft_ip_20261112/ip_probe_top.v').read_text().split('(* box_type=')[1]
(BUILD/'ip_stub.v').write_text('(* box_type='+stub)
top="""// Resource probe, NOT a deployable UART result protocol.
// Diagnostic output buses keep all processing observable.
// DSP starts only after uploaded IQ has been fully read back and ACKed.
// Host must remain quiescent during DSP: busy-NACK/RESULT integration absent.
module ip_resource_top(input clk,rst,uart_rxd,start,out_ready,
 output uart_txd,active_session,busy,done,error,saturation_sticky,
 output out_valid,output [9:0] out_record_id,output [6:0] out_range,
 output [4:0] out_bin,output signed [5:0] out_signed_bin,
 output [45:0] out_peak_power,output [11:0] out_cluster_cells,
 output out_tie_flag,output [11:0] out_equal_power_cells,
 output power_valid,output [45:0] power_value,
 output [6:0] power_range,output [4:0] power_bin);
 wire [12:0] addr;wire [31:0] word;
 wire [14:0] uploaded,readback;
 wire launch=start && active_session && uploaded==16896 && readback==16896 && !busy;
 uart_s05_shared_resource_probe u_link(.clk(clk),.rst(rst),
 .uart_rxd(uart_rxd),.uart_txd(uart_txd),.active_session(active_session),
 .expected_seq(),.activation_count(),.accepted_count(),.duplicate_count(),
 .stale_count(),.nack_count(),.good_frames(),.crc_errors(),.header_errors(),
 .length_errors(),.partial_timeouts(),.uart_errors(),.cpi_open(),.cpi_id(),
 .iq_uploaded_bytes(uploaded),.iq_readback_acked_bytes(readback),
 .tx_next_seq(),.tx_retry_exhausted(),.dsp_mem_active(busy),
 .dsp_read_addr(addr),.dsp_read_word(word));
 radar_cpi_core u_core(.clk(clk),.rst(rst),.start(launch),
 .iq_read_addr(addr),.iq_read_word(word),.out_valid(out_valid),.out_ready(out_ready),
 .out_record_id(out_record_id),.out_range(out_range),.out_bin(out_bin),
 .out_signed_bin(out_signed_bin),.out_peak_power(out_peak_power),
 .out_cluster_cells(out_cluster_cells),.out_tie_flag(out_tie_flag),
 .out_equal_power_cells(out_equal_power_cells),.busy(busy),.done(done),
 .error(error),.saturation_sticky(saturation_sticky),
 .power_valid(power_valid),.power_value(power_value),
 .power_range(power_range),.power_bin(power_bin));endmodule
"""
common=['common/rne_sat_signed','mf16/mf16_coeff_rom','mf16/mf16_serial_mac','mti/mti2_diff','power_cfar/power_q25_u46_serial']
uart_sources=['uart_rx_8n1','uart_tx_8n1','s02_frame_echo','s02_r1_reply_tx','s05_iq_cpi_banked','s05_session_arq']
base_core=ROOT/'rtl/integration/radar_cpi_core.v'
no_group=ROOT/'engineering/evidence/s05/feasibility-20261112/no_group/cfar_grouping_subsystem.v'
no_cfar=ROOT/'engineering/evidence/s05/feasibility-20261112/no_cfar_group/radar_cpi_core.v'
for name in ['power','cfar','grouping']:
 p=BUILD/name;p.mkdir(exist_ok=True)
 (p/'ip_resource_top.v').write_text(top)
 (p/'radar_cpi_core.v').write_bytes((no_cfar if name=='power' else base_core).read_bytes())
 sources=[ROOT/f'rtl/{v}.v' for v in common]
 if name!='power':sources += [ROOT/'rtl/power_cfar/cfar_compare.v',ROOT/'rtl/power_cfar/cfar_2d_scan.v']
 if name=='cfar':sources+=[no_group]
 if name=='grouping':sources += [ROOT/'rtl/grouping/grouping_8conn.v',ROOT/'rtl/integration/cfar_grouping_subsystem.v']
 sources += [ROOT/f'rtl/uart/{v}.v' for v in uart_sources]
 sources += [EXP/'fft32_ip_adapter.v',BUILD/'ip_stub.v',BUILD/'uart_shared_probe.v',p/'radar_cpi_core.v',p/'ip_resource_top.v']
 (p/'probe.prj').write_text(''.join(f'verilog work {v}\n' for v in sources))
 (p/'probe.xst').write_text(f'run\n-ifn {p}/probe.prj\n-ifmt mixed\n-ofn {p}/ip_resource_top.ngc\n-p xc6slx9-2-ftg256\n-top ip_resource_top\n-opt_mode Area\n-opt_level 2\n-keep_hierarchy No\n-rtlview No\n')
 (p/'probe.ucf').write_text('NET "clk" TNM_NET = "clk_group";\nTIMESPEC "TS_clk" = PERIOD "clk_group" 20 ns HIGH 50%;\n')
# Arithmetic-preserving pipeline and RAM candidates; preserve the failed
# local-clock variant as negative evidence, then explicitly share one BUFG.
for name,base in [('cfar_pipelined','cfar'),('grouping_ram_pipelined','grouping'),('grouping_ram_globalclock','grouping')]:
 p=BUILD/name;p.mkdir(exist_ok=True);src=BUILD/base
 text=(src/'probe.prj').read_text().replace(str(src),str(p))
 text=text.replace(str(ROOT/'rtl/mf16/mf16_serial_mac.v'),str(EXP/'mf16_serial_mac_pipelined_probe.v'))
 text=text.replace(str(ROOT/'rtl/uart/s05_iq_cpi_banked.v'),str(EXP/'s05_iq_cpi_banked_registered_probe.v'))
 if name.startswith('grouping_ram'):
  text=text.replace(str(ROOT/'rtl/grouping/grouping_8conn.v'),str(EXP/'grouping_8conn_ram_probe.v'))
 (p/'probe.prj').write_text(text)
 (p/'probe.xst').write_text((src/'probe.xst').read_text().replace(str(src),str(p)))
 for f in ['radar_cpi_core.v','probe.ucf']:(p/f).write_bytes((src/f).read_bytes())
 top=(src/'ip_resource_top.v').read_text()
 if name.endswith('globalclock'):
  top=top.replace(' wire [12:0] addr;', ' wire clk_g;\n BUFG u_global_clock(.I(clk),.O(clk_g));\n wire [12:0] addr;').replace('.clk(clk)', '.clk(clk_g)')
 (p/'ip_resource_top.v').write_text(top)
print(BUILD)

