module systolic_pe(
  clk, reset, cntrl,
  i_stb, o_stb, i_busy, o_busy,
  data_in, weight_in, acc_in,
  acc_out, data_out, weight_out
);

  parameter data_size = 8;
  parameter acc_width = 32;
  
  initial r_busy = 1'b0;
  initial o_stb = 1'b0;
  initial o_busy = 1'b0;

  input wire clk;
  input wire reset;
  input wire cntrl;
  input wire i_stb;
  input wire i_busy;

  input [data_size - 1:0] data_in;
  input [data_size - 1:0] weight_in;
  input [acc_width - 1:0] acc_in;

  output reg [acc_width - 1:0] acc_out;
  output reg [data_size - 1:0] data_out;
  output reg [data_size - 1:0] weight_out;
  output reg o_stb;
  output reg o_busy;

  reg [data_size + data_size - 1:0] mul_reg;
  reg [acc_width - 1:0] acc_reg;
  reg [data_size - 1:0] weight_reg;

always @(posedge clk) begin

  if (reset)
  begin
    r_busy <= 1'b0;
    o_stb <= 1'b0;
    acc_reg <= 0;
    mul_reg <= 0;
    weight_reg <= 0;
  end if (!o_busy)
    o_stb <= 0;
    if (i_stb)
    begin
      r_busy <= 1'b1;
      weight_reg <= weight_in; 
      data_reg <= data_in;

      mul_reg <= data_in * weight_reg;
      acc_reg <= acc_in + mul_reg;
    end else if ((o_stb)&&(!i_busy))
    begin

      r_busy <= 1'b0;
      o_stb <= 1'b0;
  
    end else if (!o_stb) begin 

      if (r_busy) begin
        o_stb <= 1'b1;

        acc_out <= acc_reg;
        data_out <= data_reg;
        weight_out <= weight_reg;

      end
    end
  end
  
  assign o_busy = (r_busy) && (!o_stb || i_busy);

endmodule // systolic_pe