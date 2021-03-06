; Copyright 2013, Sinclair R.F., Inc.
; Copyright 2019, Rodney Sinclair
;
; Test bench for AXI4-Lite slave dual-port-ram peripheral.

.macro pushByte

.main

  ;
  ; Set the dual-port-ram to the non-zero value 0xAB from the bottom to the top.
  ;

  0 :clear
    ; write the address
    O_DP_ADDRESS outport
    ; write the value 0xAB to the memory
    0xAB .outport(O_DP_WRITE)
    ; increment the memory address
    1+
    ; compare the pointer to the length of the memory
    dup .pushByte(${2**size['axi_lite_awaddr']},0) ^
    .jumpc(clear) drop

  ; Wait up to 128 iterations for the AXI master to write a 4 to address 16
  0x10 .outport(O_DP_ADDRESS)
  ${128-1} :wait_4
    .inport(I_DP_READ) 4 - 0= .jumpc(wait_4_done) .jumpc(wait_4,1-) drop .outstrobe(O_DONE) :wait_4_inf .jump(wait_4_inf)
  :wait_4_done
  drop

  ; Read and output the first 20 memory addresses starting with address 0.
  ; Note:  The micro controller address requires one clock cycle between the
  ;        "outport" and the ".inport" for the address to fully register in the
  ;        dual-port memory.  Removing the "nop" will cause this test bench to
  ;        fail.
  0 ${20-1} :read >r
    O_DIAG_ADDR outport
    .outport(O_DP_ADDRESS,nop)
    .inport(I_DP_READ) .outport(O_DIAG_DATA)
    1+ r> .jumpc(read,1-) drop

  ; Terminate the program.
  .outstrobe(O_DONE)

  :infinite .jump(infinite)
