# typesys.py
typenames = { 'integer', 'float', 'boolean', 'char', 'string' }

_bin_ops = {
	('integer', '+', 'integer') : 'integer',
	('integer', '-', 'integer') : 'integer',
	('integer', '*', 'integer') : 'integer',
	('integer', '/', 'integer') : 'integer',
	('integer', '%', 'integer') : 'integer',
 
	('integer', '=', 'integer') : 'integer',
	('integer', '<', 'integer')  : 'boolean',
	('integer', '<=', 'integer') : 'boolean',
	('integer', '>', 'integer')  : 'boolean',
	('integer', '>=', 'integer') : 'boolean',
	('integer', '==', 'integer') : 'boolean',
	('integer', '!=', 'integer') : 'boolean',
 
	('float', '+', 'float') : 'float',
	('float', '-', 'float') : 'float',
	('float', '*', 'float') : 'float',
	('float', '/', 'float') : 'float',
	('float', '%', 'float') : 'float',
	('float', '=', 'float') : 'float',
 
	('float', '<', 'float')  : 'boolean',
	('float', '<=', 'float') : 'boolean',
	('float', '>', 'float')  : 'boolean',
	('float', '>=', 'float') : 'boolean',
	('float', '==', 'float') : 'boolean',
	('float', '!=', 'float') : 'boolean',
	
	('integer', '+', 'float') : 'float',
	('integer', '-', 'float') : 'float',
	('integer', '*', 'float') : 'float',
	('integer', '/', 'float') : 'float',
	('integer', '%', 'float') : 'float',
 
	('integer', '=', 'float') : 'float',
	('integer', '<', 'float')  : 'boolean',
	('integer', '<=', 'float') : 'boolean',
	('integer', '>', 'float')  : 'boolean',
	('integer', '>=', 'float') : 'boolean',
	('integer', '==', 'float') : 'boolean',
	('integer', '!=', 'float') : 'boolean',
 
	('float', '+', 'integer') : 'float',
	('float', '-', 'integer') : 'float',
	('float', '*', 'integer') : 'float',
	('float', '/', 'integer') : 'float',
	('float', '%', 'integer') : 'float',
	('float', '=', 'integer') : 'float',
 
	('float', '<', 'integer')  : 'boolean',
	('float', '<=', 'integer') : 'boolean',
	('float', '>', 'integer')  : 'boolean',
	('float', '>=', 'integer') : 'boolean',
	('float', '==', 'integer') : 'boolean',
	('float', '!=', 'integer') : 'boolean',
 
	('boolean', '&&', 'boolean') : 'boolean',
	('boolean', '||', 'boolean') : 'boolean',
	('boolean', '==', 'boolean') : 'boolean',
	('boolean', '!=', 'boolean') : 'boolean',
 
	('char', '=', 'char')  : 'char',
	('char', '<', 'char')  : 'boolean',
	('char', '<=', 'char') : 'boolean',
	('char', '>', 'char')  : 'boolean',
	('char', '>=', 'char') : 'boolean',
	('char', '==', 'char') : 'boolean',
	('char', '!=', 'char') : 'boolean',
 
	('string', '+', 'string') : 'string',
	('string', '=', 'string') : 'string',
}

_unary_ops = {
	('+', 'integer') : 'integer',
	('-', 'integer') : 'integer',
	('^', 'integer') : 'integer',
	('+', 'float')   : 'float',
	('-', 'float')   : 'float',
	('!', 'boolean') : 'boolean',
}

def loockup_type(name):
	if name in typenames:
		return name
	return None

def check_binop(op, left_type, right_type):
	return _bin_ops.get((left_type, op, right_type))

def check_unaryop(op, operand_type):
	return _unary_ops.get((op, operand_type))