# Copyright 2014, Sinclair R.F., Inc.

def push32(ad):
  """
  User-defined macro to push a 32 bit value onto the data stack so that the LSB
  is deepest in the data stack and the MSB is at the top of the data stack.
  Usage:
    .push32(v)
  where
    v           is a 32-bit value, a constant, or an evaluated expression\n
  The effect is to push v%0x100, int(v/2**8)%0x100, int(v/2**16)%0x100, and
  int(v/2**24)%0x100 onto the data stack.\n
  ( - u_LSB u u u_MSB )
  """

  # Add the macro to the list of recognized macros.
  ad.AddMacro('.push32', 4, [ ['','singlevalue','symbol'] ]);

  # Define the macro functionality.
  def emitFunction(ad,fp,argument):
    argument = argument[0];
    v = ad.Emit_IntegerValue(argument);
    if not (-2**31 <= v < 2**32):
      raise asmDef.AsmException('Argument "%s" should be a 32-bit integer at %s' % (argument['value'],argument['loc'],));
    printString = argument['value'] if type(argument['value']) == str else '0x%04X' % (v % 2**32);
    for ix in range(4-1):
      ad.EmitPush(fp,v%0x100,'');
      v >>= 8;
    ad.EmitPush(fp,v%0x100,'.push32(%s)' % printString);

  ad.EmitFunction['.push32'] = emitFunction;
