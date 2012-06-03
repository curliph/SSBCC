################################################################################
#
# Copyright 2012, Sinclair R.F., Inc.
#
# Verilog generation functions.
#
################################################################################

import re

from ssbccUtil import *;

################################################################################
#
# Generate the code to run the INPORT selection, the associated output
# strobes,and the set-reset latches.
#
################################################################################

def genInports(fp,config):
  if not config['inports']:
    fp.write('// no input ports\n');
    return
  haveBitInportSignals = False;
  for ix in range(len(config['inports'])):
    thisPort = config['inports'][ix][1:];
    for jx in range(len(thisPort)):
      signal = thisPort[jx];
      signalType = signal[2];
      if signalType in ('data','set-reset',):
        haveBitInportSignals = True;
  if haveBitInportSignals:
    fp.write('always @ (*)\n');
    fp.write('  case (s_T)\n');
  for ix in range(len(config['inports'])):
    thisPort = config['inports'][ix][1:];
    nBits = 0;
    bitString = '';
    for jx in range(len(thisPort)):
      signal = thisPort[jx];
      signalName = signal[0];
      signalSize = signal[1];
      signalType = signal[2];
      if signalType == 'data':
        nBits = nBits + signalSize;
        if len(bitString)>0:
          bitString = bitString + ', ';
        bitString = bitString + signalName;
      if signalType == 'set-reset':
        fp.write('      8\'h%02X : s_T_inport = (%s || s_SETRESET_%s) ? 8\'hFF : 8\'h00;\n' % (ix, signalName, signalName));
    if nBits == 0:
      pass;
    elif nBits < 8:
      fp.write('      8\'h%02X : s_T_inport = { %d\'h0, %s };\n' % (ix,8-nBits,bitString));
    elif nBits == 8:
      fp.write('      8\'h%02X : s_T_inport = %s;\n' % (ix,bitString));
    else:
      raise Exception('Program Bug -- this condition should have been caught elsewhere');
  if haveBitInportSignals:
    fp.write('    default : s_T_inport = 8\'h00;\n');
    fp.write('  endcase\n');
    fp.write('\n');
  # Generate all the INPORT strobes.
  for ix in range(len(config['inports'])):
    thisPort = config['inports'][ix][1:];
    for jx in range(len(thisPort)):
      signal = thisPort[jx];
      signalName = signal[0];
      signalType = signal[2];
      if signalType == 'strobe':
        fp.write('initial %s = 1\'b0;\n' % signalName);
        fp.write('always @ (posedge i_clk)\n');
        fp.write('  if (i_rst)\n');
        fp.write('    %s <= 1\'b0;\n' % signalName);
        fp.write('  else if (s_inport)\n');
        fp.write('    %s <= (s_T == 8\'h%02X);\n' % (signalName,ix));
        fp.write('  else\n');
        fp.write('    %s <= 1\'b0;\n' % signalName);
        fp.write('\n');
  # Generate all the INPORT "set-reset"s.
  for ix in range(len(config['inports'])):
    thisPort = config['inports'][ix][1:];
    if thisPort[0][2] == 'set-reset':
      signalName = thisPort[0][0];
      fp.write('initial s_SETRESET_%s = 1\'b0;\n' % signalName);
      fp.write('always @(posedge i_clk)\n');
      fp.write('  if (i_rst)\n');
      fp.write('    s_SETRESET_%s <= 1\'b0;\n' % signalName);
      fp.write('  else if (s_inport && (s_T == 8\'h%02X))\n' % ix);
      fp.write('    s_SETRESET_%s <= 1\'b0;\n' % signalName);
      fp.write('  else if (%s)\n' % signalName);
      fp.write('    s_SETRESET_%s <= 1\'b1;\n' % signalName);
      fp.write('  else\n');
      fp.write('    s_SETRESET_%s <= s_SETRESET_%s;\n' % (signalName,signalName));

def genInstructions(fp,programBody,config):
  nInstructions = config['nInstructions'];
  fp.write('reg [8:0] s_opcodeMemory[%d:0];\n' % (nInstructions-1));
  fp.write('initial begin\n');
  programBodyIx = 0;
  for ix in range(len(programBody)):
    if programBody[ix][0] == '-':
      fp.write('  // %s\n' % programBody[ix][2:]);
    else:
      if programBody[ix][0] == 'p':
        fp.write('  s_opcodeMemory[\'h%X] = { 1\'b1, %s[0+:8] };\n' % (programBodyIx,programBody[ix][2:]));
      else:
        fp.write('  s_opcodeMemory[\'h%X] = 9\'h%s; // %s\n' % (programBodyIx,programBody[ix][0:3],programBody[ix][4:]));
      programBodyIx = programBodyIx + 1;
  for ix in range(programBodyIx,nInstructions):
    fp.write('  s_opcodeMemory[\'h%X] = 9\'h000;\n' % ix);
  fp.write('end\n');

def genLocalParam(fp,config):
  fp.write('localparam C_PC_WIDTH                              = %4d;\n' % CeilLog2(config['nInstructions']));
  fp.write('localparam C_RETURN_PTR_WIDTH                      = %4d;\n' % CeilLog2(config['return_stack']));
  fp.write('localparam C_DATA_PTR_WIDTH                        = %4d;\n' % CeilLog2(config['data_stack']));

# TODO -- accommodate m*n architecture statements
def genMemory(fp,memories):
  for ixBank in range(4):
    if ixBank not in memories['bank']:
      continue;
    ixMem = memories['bank'].index(ixBank);
    memName = 's_mem%d' % ixBank;
    memLength = eval(memories['arch'][ixMem]);
    nMemLengthBits = CeilLog2(memLength);
    fp.write('reg [7:0] %s[%d:0];\n' % (memName,memLength-1));
    fp.write('initial begin\n');
    ixAddr = 0;
    name = None;
    for line in memories['body'][ixMem]:
      if line[0] == '-':
        name = line[2:-1];
        continue;
      fp.write('  %s[\'h%X] = 8\'h%s;' % (memName,ixAddr,line[0:2]));
      if name:
        fp.write(' // %s' % name);
        name = None;
      fp.write('\n');
      ixAddr = ixAddr + 1;
    while ixAddr < memLength:
      fp.write('  %s[\'h%X] = 8\'h00;\n' % (memName,ixAddr));
      ixAddr = ixAddr + 1;
    fp.write('end\n');
    if memories['type'][ixMem] == 'RAM':
      fp.write('always @ (posedge i_clk)\n');
      fp.write('  if (s_mem_wr && (s_opcode[0+:2] == 2\'d%d))\n' % ixBank);
      if nMemLengthBits < 8:
        fp.write('    %s[s_T[0+:%d]] <= s_N;\n' % (memName,nMemLengthBits));
      else:
        fp.write('    %s[s_T] <= s_N;\n' % memName);
    if nMemLengthBits < 8:
      fp.write('wire [7:0] s_mem%d_out = %s[s_T[0+:%d]];\n' %
      (ixBank,memName,nMemLengthBits));
    else:
      fp.write('wire [7:0] s_mem%d_out = %s[s_T];\n' % (ixBank,memName));
    fp.write('\n');
  if len(memories['list']) == 0:
    fp.write('wire [7:0] s_memory = 8\'h00;\n');
  elif len(memories['list']) == 1:
    fp.write('wire [7:0] s_memory = s_mem%d_out;\n' % memories['bank'][0]);
  else:
    fp.write('reg [7:0] s_memory = 8\'h00;\n');
    fp.write('always @ (*)\n');
    fp.write('  case (s_opcode[0+:2])\n');
    for ixBank in range(4):
      if ixBank in memories['bank']:
        fp.write('    2\'d%d : s_memory <= s_mem%d_out;\n' % (ixBank,ixBank));
    fp.write('    default : s_memory <= 8\'h00;\n');
    fp.write('  endcase\n');

def genModule(fp,outCoreName,config,parameters):
  fp.write('module %s(\n' % outCoreName);
  fp.write('  // synchronous reset and processor clock\n');
  fp.write('  input  wire           i_rst,\n');
  fp.write('  input  wire           i_clk');
  if config['ios']:
    wasComment = False;
    for ix in range(len(config['ios'])):
      signal = config['ios'][ix];
      signalName = signal[0];
      signalWidth = signal[1];
      signalType = signal[2];
      if wasComment:
        fp.write('\n');
      else:
        fp.write(',\n');
      wasComment = False;
      if signalType == 'comment':
        fp.write('  // %s' % signalName);
        wasComment = True;
      elif signalType == 'input':
        if signalWidth == 1:
          fp.write('  input  wire           %s' % signalName);
        elif signalWidth < 10:
          fp.write('  input  wire     [%d:0] %s' % (signalWidth-1,signalName));
        else:
          fp.write('  input  wire    [%2d:0] %s' % (signalWidth-1,signalName));
      elif signalType == 'output':
        if signalWidth == 1:
          fp.write('  output reg            %s' % signalName);
        elif signalWidth < 10:
          fp.write('  output reg      [%d:0] %s' % (signalWidth-1,signalName));
        else:
          fp.write('  output reg     [%2d:0] %s' % (signalWidth-1,signalName));
      else:
        raise Exception('Program Bug -- unrecoginized ios "%s"' % signalType);
  fp.write('\n');
  fp.write(');\n');
  if parameters['name']:
    fp.write('\n');
    for ix in range(len(parameters['name'])):
      fp.write('parameter [7:0] %s = 8\'h%02X;\n' % (parameters['name'][ix],int(parameters['default'][ix])));

def genOutports(fp,config):
  if not config['outports']:
    fp.write('// no output ports\n');
    return;
  for ix in range(len(config['outports'])):
    thisPort = config['outports'][ix][1:];
    for jx in range(len(thisPort)):
      signal = thisPort[jx];
      signalName = signal[0];
      signalWidth = signal[1];
      signalType = signal[2];
      if signalType == 'data':
        fp.write('initial %s = %d\'h0;\n' % (signalName,signalWidth));
        fp.write('always @ (posedge i_clk)\n');
        fp.write('  if (i_rst)\n');
        fp.write('    %s <= %d\'h0;\n' % (signalName,signalWidth));
        fp.write('  else if (s_outport && (s_T == 8\'h%02X))\n' % ix);
        fp.write('    %s <= s_N[0+:%d];\n' % (signalName,signalWidth));
        fp.write('  else\n');
        fp.write('    %s <= %s;\n' % (signalName,signalName));
        fp.write('\n');
      elif signalType == 'strobe':
        fp.write('initial %s = 1\'b0;\n' % signalName);
        fp.write('always @ (posedge i_clk)\n');
        fp.write('  if (i_rst)\n');
        fp.write('    %s <= 1\'b0;\n' % signalName);
        fp.write('  else if (s_outport)\n');
        fp.write('    %s <= (s_T == 8\'h%02X);\n' % (signalName,ix));
        fp.write('  else\n');
        fp.write('    %s <= 1\'b0;\n' % signalName);
        fp.write('\n');
      else:
        raise Exception('Program Bug -- signalType = "%s" shouldn\'t have been encountered' % signalType);

def genSignals(fp,config):
  if not config['signals']:
    fp.write('// no additional signals\n');
    return;
  maxLength = 0;
  for ix in range(len(config['signals'])):
    thisSignal = config['signals'][ix];
    signalName = thisSignal[0];
    if len(signalName) > maxLength:
      maxLength = len(signalName);
  maxLength = maxLength + 12;
  for ix in range(len(config['signals'])):
    thisSignal = config['signals'][ix];
    signalName = thisSignal[0];
    signalWidth = thisSignal[1];
    outString = 'reg ';
    if signalWidth == 1:
      outString += '       ';
    elif signalWidth < 10:
      outString += (' [%d:0] ' % (signalWidth-1));
    else:
      outString += ('[%2d:0] ' % (signalWidth-1));
    outString += signalName;
    outString += ' '*(maxLength-len(outString));
    outString += ('= %d\'d0;\n' % signalWidth);
    fp.write(outString);

def genUserHeader(fp,user_header):
  for ix in range(len(user_header)):
    fp.write('// %s\n' % user_header[ix]);
