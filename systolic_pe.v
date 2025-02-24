module systolic_pe(
  clk, reset, cntrl, data_in, weight_in, acc_in,
  acc_out, data_out, weight_out
);

  parameter data_size = 8;
  parameter acc_width = 32;

  input clk;
  input reset;
  input cntrl;

  input [data_size - 1:0] data_in;
  input [data_size - 1:0] weight_in;
  input [acc_width - 1:0] acc_in;

  output reg [acc_width - 1:0] acc_out;
  output reg [data_size - 1:0] data_out;
  output reg [data_size - 1:0] weight_out;

  reg [data_size + data_size - 1:0] mul_reg;
  reg [acc_width - 1:0] acc_reg;
  reg [data_size - 1:0] weight_reg;



  always @(posedge clk) begin
    if (reset) begin
      acc_out <= 0;
      data_out <= 0;
      mul_reg <= 0;
      acc_reg <= 0;
      weight_reg <= 0;
    end else begin
      if (cntrl) begin
        weight_reg <= weight_in;;
        weight_out <= weight_reg;
      end
      acc_out <= acc_reg;
      data_out <= data_in;
      mul_reg <= data_in * weight_in;
      acc_reg <= acc_in + mul_reg;
    end
    
  end
endmodule // systolic_pe