import nmodl.dsl as nmodl
from nmodl import ast, visitor


class Mod:
    def __init__(self, modpath):
        self.modpath = modpath
        self.ast = nmodl.NmodlDriver().parse_file(modpath)

        symv = nmodl.symtab.SymtabVisitor()
        symv.visit_program(self.ast)
        self.symbol_table = self.ast.get_symbol_table()

        self._get_var_table()

    def mechanism(self):
        a = visitor.AstLookupVisitor().lookup(self.ast, ast.AstNodeType.SUFFIX)

        if a:
            return str(nmodl.to_nmodl(a[0].type)), str(nmodl.to_nmodl(a[0].name))

        return None

    def _is_setRNG(self):
        procedure_list = visitor.AstLookupVisitor().lookup(
            self.ast, ast.AstNodeType.PROCEDURE_BLOCK
        )
        procedure_list = [nmodl.to_nmodl(i.name) for i in procedure_list]
        return "setRNG" in procedure_list

    def is_net_receive(self):
        a = visitor.AstLookupVisitor().lookup(
            self.ast, ast.AstNodeType.NET_RECEIVE_BLOCK
        )
        return bool(len(a))

    @staticmethod
    def _guess_variable_type(v):
        if v.startswith("e"):
            return "(mV)"
        if v == "v":
            return "(mV)"
        if v.startswith("i"):
            return "(mA/cm2)"

        return "(mM)"

    def get_useion_read(self):

        v = [
            i.get_name()
            for i in self.symbol_table.get_variables_with_properties(
                nmodl.symtab.NmodlType.read_ion_var, True
            )
        ]

        return {i: self.var_table[i] for i in v}

    def get_useion_write(self):

        v = [
            i.get_name()
            for i in self.symbol_table.get_variables_with_properties(
                nmodl.symtab.NmodlType.write_ion_var, True
            )
        ]

        return {i: self.var_table[i] for i in v}

    def get_nonspecific_current(self):
        v = [
            i.get_name()
            for i in self.symbol_table.get_variables_with_properties(
                nmodl.symtab.NmodlType.nonspecific_cur_var, True
            )
        ]

        return {i: self.var_table.get(i, "") for i in v}

    def _insert_in_var_table(self, node, property):
        try:
            self.var_table[nmodl.to_nmodl(node.name)][property] = nmodl.to_nmodl(
                getattr(node, property)
            )
            return True
        except (TypeError, AttributeError):
            return False

    def _fill_var_table(self, nodes):

        for i in nodes:
            name = nmodl.to_nmodl(i.name)
            self.var_table[name] = {}

            if not self._insert_in_var_table(i, "unit"):
                self.var_table[name]["unit"] = Mod._guess_variable_type(name)

            self._insert_in_var_table(i, "value")

    def _get_var_table(self):
        self.var_table = {}

        self._fill_var_table(
            visitor.AstLookupVisitor().lookup(self.ast, ast.AstNodeType.PARAM_ASSIGN),
        )

        self._fill_var_table(
            visitor.AstLookupVisitor().lookup(
                self.ast, ast.AstNodeType.ASSIGNED_DEFINITION
            )
        )
