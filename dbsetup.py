import config
import sqlite3

RENAME_STRING = "dbsetup_temp_table_rename_"

class ForeignKey(object):
    def __init__(self):
        self.table_name = None
        self.column_name = None

    @property
    def clause(self):
        return 'REFERENCES {0} ({1})'

class Column(object):
    def __init__(self):
        self.name = None
        self.type = None
        self.not_null = False
        self.default = None
        self.foreign_key = None
        
    @property
    def decl_var(self):
        decl_str = '{0} {1}'.format(self.name, self.type)
        if self.not_null:
            decl_str += ' NOT NULL'
        if self.default:
            decl_str += ' DEFAULT ({})'.self.default
        if self.foreign_key:
            decl_str += ' ' + foreign_key.clause

        return decl_str        

class Table(object):
    def __init__(self):
        self.name = None
        self.columns = []
        self.pk = ''
        self.replace_on_pk_conflict = True

    @property
    def make_cmd(self):
        varstr = ''
        for col in self.columns:
            varstr += col.decl_var + ', '
        if self.pk:
            conf_string = ' ON CONFLICT REPLACE' if self.replace_on_pk_conflict else ''
            varstr += 'PRIMARY KEY({0}){1}, '.format(self.pk, conf_string)
        if varstr:
            return "CREATE TABLE {0} ({1})".format(self.name, varstr[:-2])
        return ''

###-------------------------------------

def add_columns(db_conn, table_name, columns):
    t_name_param = (table_name,)
    for column in columns:
        db_conn.execute("ALTER TABLE ? ADD COLUMN {}".format(column.decl_var), t_name_param)  
    db_conn.commit()

def remake_table(db_conn, table):
    table_name_tuple (table.name,)
    colnames_to_copy = []
    for row in db_conn.execute("PRAGMA table_info(?)", table_name_tuple):
        colnames_to_copy.append(row['name'])
    
    temp_table_tuple = (RENAME_STRING + table.name,)
    db_conn.execute("ALTER TABLE ? RENAME TO ?", table_name_tuple + temp_table_tuple)
    db_conn.execute(table.make_cmd)
    colnames_tuple = tuple(colnames_to_copy)
    colnames_qstring = ''
    for n in colnames_tuple:
        colnames_qstring += '?,'
    
    params = table_name_tuple + colnames_tuple + colnames_tuple + temp_table_tuple
    db_conn.execute("INSERT INTO ? ({0}) SELECT {0} FROM ?".format(colnames_qstring[:-1]), params)
    db_conn.commit()      

def create_table(db_conn, table):
    #check if table exists
    t_name_param = (table.name,)
    table_found = False
    for row in db_conn.execute("SELECT name FROM sqlite_master WHERE type='table' AND name=?", t_name_param):
        table_found = True

    #if table doesn't exist, make it
    if not table_found:
        db_conn.execute(table.make_cmd)
        db_conn.commit()
    else
        print("Error: table already exists.")

##    #if table exists, check its columns. we can add missing columns, but if cols in the table don't
##    #have the right format, the only option is to make a new table and copy the data
##    else:
##        need_to_remake = False
##        missing_cols = []
##        for column in table.columns:
##            found_col = False
##            for row in db_conn.execute("PRAGMA table_info(?)", t_name_param):
##                if row['name'] == column.name:
##                    found_col = True
##                    if (row['pk'] and table.pk != row['name']) or (row['notnull'] and not column.not_null):
##                        need_to_remake = True
##                        break
##
##            if need_to_remake:
##                break
##            elif not found_col:
##                missing_cols.append(column)
##                if table.pk == column.name:
##                    need_to_remake = True
##                    break
##
##        if need_to_remake:
##            remake_table(db_conn, table)
##        else:
##            add_columns(db_conn, table.name, missing_cols)
                        
###----------------------------

    
