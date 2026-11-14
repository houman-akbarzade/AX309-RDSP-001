`timescale 1ns/1ps
module tb_core_cycles;
reg clk=0;always #10 clk=~clk;
reg rst=1,start=0;
wire [12:0] iq_addr;wire out_valid,busy,done,error,power_valid;
wire [45:0] power_value;wire [6:0] power_range;wire [4:0] power_bin;
integer power_count=0,record_count=0;time start_ns;
reg [31:0] iqmem[0:4223];reg [31:0] iqword=0;
initial $readmemh("target_iq.hex",iqmem);
always @(posedge clk)iqword<=iqmem[iq_addr];
radar_cpi_core dut(.clk(clk),.rst(rst),.start(start),.debug_read(1'b0),.debug_addr(12'd0),.debug_power(),
.iq_read_addr(iq_addr),.iq_read_word(iqword),.out_valid(out_valid),.out_ready(1'b1),
.out_record_id(),.out_range(),.out_bin(),.out_signed_bin(),.out_peak_power(),.out_cluster_cells(),
.out_tie_flag(),.out_equal_power_cells(),.busy(busy),.done(done),.error(error),.saturation_sticky(),
.power_valid(power_valid),.power_value(power_value),.power_range(power_range),.power_bin(power_bin));
always @(posedge clk) begin if(power_valid)power_count=power_count+1;if(out_valid)record_count=record_count+1;end
initial begin repeat(20)@(negedge clk);rst=0;repeat(10)@(negedge clk);start=1;start_ns=$time;
@(negedge clk);start=0;
wait(done);$display("CORE_CYCLES %0d TIME_MS_50MHZ %f POWER_EVENTS %0d RECORD_EVENTS %0d ERROR %b",($time-start_ns)/20,($time-start_ns)/1000000.0,power_count,record_count,error);$finish;
end
initial begin #100000000;$display("FAIL watchdog");$finish;end
endmodule
