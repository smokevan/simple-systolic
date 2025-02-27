`default_nettype none

module systolic_pe(
  clk, reset, cntrl,
  i_stb, o_stb, i_busy, o_busy,
  data_in, weight_in, acc_in,
  acc_out, data_out, weight_out
);

  // Paramterization of the MAC
  parameter data_size = 8;
  parameter acc_width = 32;
 
  // I/O 
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

  // Internal registers for data storage in between cycles
  reg [data_size + data_size - 1:0] mul_result; 
  reg [acc_width - 1:0] acc_reg;                 
  reg [data_size - 1:0] weight_reg;
  reg [data_size - 1:0] data_reg;
  
  // State definition for the state machine
  localparam IDLE = 3'b000;
  localparam PROCESSING1 = 3'b001;
  localparam PROCESSING2 = 3'b010;
  localparam PROCESSING3 = 3'b011;
  localparam OUTPUT_READY = 3'b100;
  reg [2:0] state;

  // Main state machine
  always @(posedge clk) begin
    if (reset) begin
      // Reset all registers
      o_stb <= 1'b0;
      o_busy <= 1'b0;
      acc_reg <= 0;
      mul_result <= 0;
      weight_reg <= 0;
      data_reg <= 0;
      state <= IDLE;
      acc_out <= 0;
      data_out <= 0;
      weight_out <= 0;
    end
    else begin
      case (state)
        IDLE: begin
          // In IDLE state, ready to accept new data
          o_stb <= 1'b0;  // Not ready to output anything yet tho
          
          if (i_stb) begin
            // Input transaction - capture input data from upstream
            data_reg <= data_in;
            weight_reg <= weight_in;
            acc_reg <= acc_in;
            o_busy <= 1'b1;  // Signal module busy now
            state <= PROCESSING1;
          end
          else begin
            o_busy <= 1'b0;  // Not busy, ready for more data
          end
        end

        PROCESSING1: begin
          // Perform multiply-accumulate operation
          mul_result <= data_reg * weight_reg;          
          
          // Move to second processing state
          state <= PROCESSING2;
        end

        PROCESSING2: begin
          acc_reg <= acc_in + mul_result;  // Use the mul_result from previous cycle
          state <= PROCESSING3;
        end

        PROCESSING3: begin
          acc_out <= acc_reg; // Output the accumulated result
          data_out <= data_reg; // Output the data
          weight_out <= weight_reg; // Output the weight
          o_stb <= 1'b1;  // Output is ready
          state <= OUTPUT_READY; // Move to output ready state
        end
        
        OUTPUT_READY: begin
          // Wait for downstream module to accept our output
          if (!i_busy) begin
            // Output transaction occurred
            o_stb <= 1'b0;
            if (i_stb) begin
              // New input is available, start processing it
              data_reg <= data_in;
              weight_reg <= weight_in;
              acc_reg <= acc_in;
              state <= PROCESSING1;
            end
            else begin
              // No new input, return to IDLE
              o_busy <= 1'b0;
              state <= IDLE;
            end
          end else begin
            o_stb <= 1'b1;
            state <= OUTPUT_READY;
            // Remain in OUTPUT_READY state if downstream is busy
          end
        end
        
        default: state <= IDLE;
      endcase
    end
  end
  
endmodule