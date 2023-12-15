#!/usr/bin/env python3

import gi
from sys import argv
from datetime import date
import json

gi.require_version("Gtk", "4.0")

from gi.repository import Gtk

"""
    . objetivo
        . uma aplicação para guardar as minhas senhas em sites com logins
        . uma aplicação para pesquisar as minhas contas e senhas

    . funcionalidades
        . cadastrar senha, site e login
        . mostrar os logins e senhas para determinado site
        . pesquisar por site
        . editar login e senha

                             LOGO

      [             ] [adicionar]
      -------------------------------------------------------
      site    | username      | password | modified

      twitter | ThiagoFBastos | *********| 2023-08-04
      -------------------------------------------------------
      site              [                          ]
      username          [                          ]
      password          [                          ]
      [editar]          [remover]
"""

class Database:
    
    # depois tenho que encriptar as senhas

    def __init__(self):
        self._keywords = dict()
 
        with open('database.txt', 'r') as f:
            for line in f.readlines():
                keys = line.replace('\n', '').split('\t')
                if len(keys) == 0: continue
                key = tuple(keys[:2])
                value = tuple(keys[2:])
                self._keywords[key] = value

    def close(self):
        with open('database.txt', 'w') as f:
            for site, username in self._keywords:
                password, modified = self._keywords[(site, username)]
                f.write(f'{site}\t{username}\t{password}\t{modified}\n')
        
    def remove(self, site, username):
        self._keywords.pop((site, username))

    def contains(self, site, username):
        return (site, username) in self._keywords

    def add(self, site, username, password, modified):
        self._keywords[(site, username)] = (password, modified)

    def get_keywords(self):
        columns = []
        for site, username in self._keywords:
            password, modified = self._keywords[(site, username)]
            columns.append((site, username, password, modified))
        return columns

class AddWindow(Gtk.Window):
    def __init__(self, database):
        super().__init__()

        self.set_modal(True)
        self.set_title('cadastrar senha')
        self.set_default_size(300, 300)
        self.set_resizable(False)

        self.database = database

        self.cad_grid = Gtk.Grid()
        self.cad_grid.set_row_spacing(5)
        self.cad_grid.set_column_spacing(5)
        self.cad_grid.set_column_homogeneous(True)

        self.site_label = Gtk.Label(label = 'Site')
        self.site_entry = Gtk.Entry()
        self.cad_grid.attach(self.site_label, 0, 0, 5, 5)
        self.cad_grid.attach_next_to(self.site_entry, self.site_label,  Gtk.PositionType.RIGHT, 10, 5)

        self.username_label = Gtk.Label(label = 'Username')
        self.username_entry = Gtk.Entry()
        self.cad_grid.attach_next_to(self.username_label, self.site_label,  Gtk.PositionType.BOTTOM , 5, 5)
        self.cad_grid.attach_next_to(self.username_entry, self.username_label,  Gtk.PositionType.RIGHT, 10, 5)
        
        self.password_label = Gtk.Label(label = 'Password')
        self.password_entry = Gtk.Entry()
        self.cad_grid.attach_next_to(self.password_label, self.username_label,  Gtk.PositionType.BOTTOM , 5, 5)
        self.cad_grid.attach_next_to(self.password_entry, self.password_label,  Gtk.PositionType.RIGHT, 10, 5)

        self.cad_button = Gtk.Button(label = 'cadastrar')
        self.cad_button.connect('clicked', self.on_cad_button_clicked)

        self.cad_grid.attach_next_to(self.cad_button, self.password_label,  Gtk.PositionType.BOTTOM , 5, 5)
        
        self.set_child(self.cad_grid)

    def on_cad_button_clicked(self, button):
        
        site = self.site_entry.get_text()
        username = self.username_entry.get_text()
        password = self.password_entry.get_text()
        modified = str(date.today())

        if self.database.contains(site, username):
            print('a combinação de valores já está em uso')
            return

        self.database.add(site, username, password, modified)
       
class DialogWindow(Gtk.Window):
    def __init__(self, title, text):
        super().__init__()

        self.set_modal(True)

        self._confirmed = None

        self.set_title(title)
        self.box = Gtk.Box(orientation = Gtk.Orientation.VERTICAL)
        self.set_child(self.box)

        self.message = Gtk.Label(label = text)
        self.box.append(self.message)

        self.buttons_box = Gtk.Box(orientation = Gtk.Orientation.HORIZONTAL, spacing = 5)
        self.box.append(self.buttons_box)

        self.confirm_button = Gtk.Button(label = 'confirmar')
        self.confirm_button.connect('clicked', self.on_confirm_button_clicked)
        self.buttons_box.append(self.confirm_button)

        self.cancel_button = Gtk.Button(label = 'cancelar')
        self.cancel_button.connect('clicked', self.on_cancel_button_clicked)
        self.buttons_box.append(self.cancel_button)
        
    def on_confirm_button_clicked(self, button):
        self._confirmed = True
        self.close()

    def on_cancel_button_clicked(self, button):
        self._confirmed = False
        self.close()

    def getConfirmed(self):
        return self._confirmed

class MainWindow(Gtk.ApplicationWindow):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.database = Database()

        self.set_title('PassLocker')
        self.set_default_size(400, 400)
        self.set_resizable(False)
        self.connect('close-request', self.on_close_request)

        self.box = Gtk.Box(orientation = Gtk.Orientation.VERTICAL)
        self.search_box = Gtk.Box(orientation = Gtk.Orientation.HORIZONTAL, spacing = 5, )

        self.set_child(self.box)
        self.box.append(self.search_box)

        self.entry_search = Gtk.Entry()
        self.entry_search.connect('changed', self.on_changed_entry_search)
        self.search_box.append(self.entry_search)

        self.btn_add = Gtk.Button(label = 'adicionar')
        self.btn_add.connect('clicked', self.on_add_button_clicked)
        self.search_box.append(self.btn_add)

        self.liststore = Gtk.ListStore(str, str, str, str)
        self.sort_tree_model = Gtk.TreeModelSort(model = self.liststore)
        self.sort_tree_model.set_sort_column_id(0, Gtk.SortType.ASCENDING)

        for line in self.database.get_keywords():
            self.liststore.append(list(line))

        self.treeview = Gtk.TreeView(model = self.sort_tree_model)

        self.renderer_site = Gtk.CellRendererText()
        column_site = Gtk.TreeViewColumn('site', self.renderer_site, text = 0) 
        self.treeview.append_column(column_site)
    
        self.renderer_username = Gtk.CellRendererText()
        column_username = Gtk.TreeViewColumn('username', self.renderer_username, text = 1) 
        self.treeview.append_column(column_username)

        self.renderer_password = Gtk.CellRendererText()
        column_password = Gtk.TreeViewColumn('password', self.renderer_password, text = 2)
        self.treeview.append_column(column_password)

        self.renderer_modified = Gtk.CellRendererText()
        column_modified = Gtk.TreeViewColumn('modified', self.renderer_modified, text = 3)
        self.treeview.append_column(column_modified)

        tree_selection = self.treeview.get_selection()
        tree_selection.set_mode(Gtk.SelectionMode.SINGLE)
        tree_selection.connect('changed', self.on_selection_changed)

        self.scroll = Gtk.ScrolledWindow()
        self.scroll.set_child(self.treeview)
        self.scroll.set_min_content_height(300)
        self.scroll.set_policy(Gtk.PolicyType.AUTOMATIC, Gtk.PolicyType.AUTOMATIC)

        self.box.append(self.scroll)

        self.edit_grid = Gtk.Grid()
        self.edit_grid.set_row_spacing(1)
        self.edit_grid.set_column_spacing(1)
        self.edit_grid.set_column_homogeneous(True)
        self.edit_grid.set_row_homogeneous(True)

        self.site_label = Gtk.Label(label = 'Site')
        self.site_entry = Gtk.Entry()
        self.edit_grid.attach(self.site_label, 0, 0, 5, 5)
        self.edit_grid.attach_next_to(self.site_entry, self.site_label,  Gtk.PositionType.RIGHT, 10, 5)

        self.username_label = Gtk.Label(label = 'Username')
        self.username_entry = Gtk.Entry()
        self.edit_grid.attach_next_to(self.username_label, self.site_label,  Gtk.PositionType.BOTTOM , 5, 5)
        self.edit_grid.attach_next_to(self.username_entry, self.username_label,  Gtk.PositionType.RIGHT, 10, 5)
        
        self.password_label = Gtk.Label(label = 'Password')
        self.password_entry = Gtk.Entry()
        self.edit_grid.attach_next_to(self.password_label, self.username_label,  Gtk.PositionType.BOTTOM , 5, 5)
        self.edit_grid.attach_next_to(self.password_entry, self.password_label,  Gtk.PositionType.RIGHT, 10, 5)

        self.edit_button = Gtk.Button(label = 'editar')
        self.edit_button.connect('clicked', self.on_edit_button_clicked)

        self.delete_button = Gtk.Button(label = 'deletar')
        self.delete_button.connect('clicked', self.on_delete_button_clicked)

        self.edit_grid.attach_next_to(self.edit_button, self.password_label,  Gtk.PositionType.BOTTOM , 5, 5)
        self.edit_grid.attach_next_to(self.delete_button, self.edit_button,  Gtk.PositionType.RIGHT, 5, 5)        

        self.box.append(self.edit_grid)

    def on_close_request(self, window):
        self.database.close()

    def on_selection_changed(self, selection):
        model, it = selection.get_selected()

        if it == None:
            return

        site = model.get_value(it, 0)
        username = model.get_value(it, 1)
        password = model.get_value(it, 2)

        self.site_entry.set_text(site)
        self.username_entry.set_text(username)
        self.password_entry.set_text(password)

    def on_edit_button_clicked(self, button):
        
        model, it = self.treeview.get_selection().get_selected()

        if it == None: return

        old_site = model.get_value(it, 0)
        old_username = model.get_value(it, 1)
        old_password = model.get_value(it, 2)

        new_site = self.site_entry.get_text()
        new_username = self.username_entry.get_text()
        new_password = self.password_entry.get_text()
        new_modified = str(date.today())

        if (old_site, old_username) == (new_site, new_username):
            if old_password == new_password:
                print('a senha já está em uso')
                return
        elif self.database.contains(new_site, new_username):
            print('essa combinação de valores já está em uso')
            return
    
        self.database.remove(old_site, old_username)
        self.database.add(new_site, new_username, new_password, new_modified)
        self.liststore.set(it, [0, 1, 2, 3], [new_site, new_username, new_password, new_modified])   
    
    def delete_action(self, dialog):
        if dialog.getConfirmed(): 

            smodel, it = self.treeview.get_selection().get_selected()

            if it is None: return

            it = self.sort_tree_model.convert_iter_to_child_iter(it)
            model = smodel.get_model()

            site = model.get_value(it, 0)
            username = model.get_value(it, 1)

            self.database.remove(site, username)
            self.liststore.remove(it)

    def on_delete_button_clicked(self, button):
        dialog = DialogWindow('confirmação', 'deseja excluir permanentemente esse dado?')
        dialog.present()
        dialog.connect('close_request', self.delete_action)
        
    def on_changed_entry_search(self, entry):
        text = entry.get_text()
        
        self.liststore.clear()

        for site, username, password, modified in self.database.get_keywords():
            if site.startswith(text):
                self.liststore.append([site, username, password, modified])

    def on_add_window_close_request(self, window):
        self.liststore.clear()
        for line in self.database.get_keywords():
            self.liststore.append(list(line))

    def on_add_button_clicked(self, button):
        self.add_window = AddWindow(self.database)
        self.add_window.connect('close_request', self.on_add_window_close_request)
        self.add_window.present()

class MyApp(Gtk.Application):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.connect('activate', self.on_activate)

    def on_activate(self, app):
        self.win = MainWindow(application = app)
        self.win.present()

app = MyApp(application_id = "com.app.passlocker")
app.run(argv)

