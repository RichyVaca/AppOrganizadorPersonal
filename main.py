import webapp2

#3 metodo
import os
import jinja2
import random
import logging

from google.appengine.ext import ndb
from webapp2_extras import sessions
from Crypto.Hash import SHA256

usuario = ''
psw = ''
consulta = ''
idTarea = 1
idTarea2 = 0
idEvento = 1
idEvento2 = 0
idContacto = 1
idContacto2 = 0
listaTareas = []
modificar = False

template_dir = os.path.join(os.path.dirname(__file__), 'templates')
jinja_env = jinja2.Environment(loader = jinja2.FileSystemLoader(template_dir),
                               autoescape = True)
template_values={}

def render_str(template,**params):
    t = jinja_env.get_template(template)
    return t.render(params)

class Handler(webapp2.RequestHandler):
    def dispatch(self):
        self.session_store = sessions.get_store(request=self.request)

        try:
            # Dispatch the request.
            webapp2.RequestHandler.dispatch(self)
        finally:
            # Save all sessions.
            self.session_store.save_sessions(self.response)
    
    @webapp2.cached_property
    def session(self):
        return self.session_store.get_session()
    def render(self,template,**kw):
        self.response.out.write(render_str(template, **kw))
    def write(self,*a,**kw):
        self.response.out.write(*a,**kw)

class Eventos(ndb.Model):
    idEvento = ndb.IntegerProperty()
    titleEvento = ndb.StringProperty()
    fechaInicio = ndb.StringProperty()
    fechaFin = ndb.StringProperty()
    descriptionEvento = ndb.StringProperty()

class Tareas(ndb.Model):
    title = ndb.StringProperty()
    description = ndb.StringProperty()
    idTarea = ndb.IntegerProperty()

class Contactos(ndb.Model):
    idContacto = ndb.IntegerProperty()
    name = ndb.StringProperty()
    phone = ndb.StringProperty()
    fechaNacimiento = ndb.StringProperty()
    address = ndb.StringProperty()
    email = ndb.StringProperty()

class Cuentas(ndb.Model):
    username = ndb.StringProperty()
    password = ndb.StringProperty()
    tarea = ndb.StructuredProperty(Tareas, repeated=True)
    contacto = ndb.StructuredProperty(Contactos, repeated=True)
    evento = ndb.StructuredProperty(Eventos, repeated=True)



class Login(Handler):
    def get(self):
        self.render("index.html")
    def post(self):
        global template_values
        global consulta
        usuario = self.request.get('username')
        psw = self.request.get('password')
        psw = SHA256.new(psw).hexdigest()

        logging.info('Checando usuario ='+str(usuario) + 'psw= ' + str(psw))
        msg = ''
        if psw == '' or usuario == '':
            msg = 'Please specify Account and Password'
            self.render("index.html", error = msg)
        else:
            consulta=Cuentas.query(ndb.AND(Cuentas.username==usuario, Cuentas.password==psw )).get()
            if consulta is not None:
                logging.info('POST consulta=' + str(consulta))

                self.session['username'] = consulta.username
                logging.info("%s just logged in" % usuario)
                template_values={
                    'username': self.session['username']
                }
                self.render("principal.html", user = template_values)
                
            else:
                logging.info('POST consulta=' + str(consulta))
                msg = 'Incorrect user or password.. please try again'
                self.render("index.html", error = msg)
    

class Registro(Handler):
    def get(self):
        self.render("registro.html")
    def post(self):
        global usuario
        global psw
        usuario = self.request.get('username')
        psw = self.request.get('password')
        psw = SHA256.new(psw).hexdigest()

        cuenta = Cuentas(username = usuario, password = psw)

        cuentaKey = cuenta.put()

        cuenta_usuario = cuentaKey.get()

        if cuenta_usuario == cuenta:
            print "cuenta de usuario ", cuenta_usuario
            msg = "Gracias por registrarse"
            self.render("registro.html", error = msg)
        self.redirect("/")


class Logout(Handler):
    def get(self):
        if self.session.get('username'):
            msg = ''
            self.render("index.html", error = msg)
            del self.session['username']

class TareasP(Handler):
    def get(self):
        global consulta
        global template_values
        global modificar
        lista = []
        for i in consulta.tarea:
            lista.append(i)
        self.render("tareas.html", user = template_values, lista = lista)
    def post(self):
        global consulta
        global idTarea
        global template_values
        global modificar
        idTarea2 = self.request.get('idTarea')
        title = self.request.get('nombreTarea')
        description = self.request.get('nota')
        #consulta=Cuentas.query(ndb.AND(Cuentas.username==usuario, Cuentas.password==psw )).get()
        if consulta is not None:
            contador = 0
            for i in consulta.tarea:
                idTarea = idTarea + 1
                if modificar == True:
                    if int(idTarea2) == i.idTarea:
                        consulta.tarea.pop(contador)
                        consulta.put()
                        idTarea2 = 0
                        modificar = False
                        break
                contador += 1
            nueva_tarea=Tareas(title = title, description = description, idTarea = idTarea)
            consulta.tarea.append(nueva_tarea)
            consulta.put()
            lista = []
            for i in consulta.tarea:
                lista.append(i)
            self.render("tareas.html",user = template_values, lista = lista)
            idTarea = 1
            idTarea2 = "0"
class EditarTarea(Handler):        
    def post(self):
        global idTarea2
        global consulta
        global listaTareas
        global template_values
        global modificar
        usuario = self.session['username']
        boton_modificar = self.request.get("modificar")
        boton_eliminar = self.request.get("eliminar")
        idTarea2 = self.request.get("idTarea_input")
        title = self.request.get("title_input")
        description = self.request.get("description_input")
        if boton_modificar == "Modificar":
            self.render("tareas.html",user = template_values, idTarea = idTarea2, title  = title, description = description)
            modificar = True
        if boton_eliminar == "Eliminar":
            if consulta is not None:
                contador = 0
                global consulta
                for i in consulta.tarea:
                    if int(idTarea2) == i.idTarea:
                        consulta.tarea.pop(contador)
                        consulta.put()
                        idTarea2 = 0
                        break
                    contador += 1
            lista = []
            global consulta
            for i in consulta.tarea:  
                lista.append(i)
            self.render("tareas.html",user = template_values, lista = lista)
class EventosP(Handler):
    def get(self):
        global consulta
        global idEvento
        global template_values
        global modificar
        lista = []
        for i in consulta.evento:
            lista.append(i)
        self.render("eventos.html",user = template_values, lista = lista)
    def post(self):
        global consulta
        global idEvento
        global template_values
        global modificar
        idEvento2 = self.request.get("idEvento")
        titleEvento = self.request.get("titleEvento")
        fechaI = self.request.get("fechaI")
        fechaF = self.request.get("fechaF")
        decriptionEvento = self.request.get("descriptionEvento")
        if consulta is not None:
            contador = 0
            for i in consulta.evento:
                idEvento = idEvento  + 1
                if modificar == True:
                    if int(idEvento2) == i.idEvento:
                        consulta.evento.pop(contador)
                        consulta.put()
                        idEvento2 = 0
                        modificar = False
                        break
                contador += 1
            nuevo_evento = Eventos(idEvento = idEvento, titleEvento = titleEvento, fechaInicio = fechaI, fechaFin = fechaF, descriptionEvento = decriptionEvento)
            consulta.evento.append(nuevo_evento)
            consulta.put()
            lista = []
            for i in consulta.evento:
                lista.append(i)
            self.render("eventos.html",user = template_values, lista = lista)
            idEvento = 1
            idEvento2 = "0"
class EditarEventos(Handler):
    def post(self):
        global consulta
        global template_values
        global idEvento2
        global modificar
        idEvento2 = self.request.get("idEvento_input")
        titleEvento = self.request.get("titleEvento_input")
        fechaI = self.request.get("fechaInicio_input")
        fechaF = self.request.get("fechaFin_input")
        descrptionEvento = self.request.get("descriptionEvento_input")
        boton_modificar = self.request.get("modificar")
        boton_eliminar = self.request.get("eliminar")
        if boton_modificar == "Modificar":
            self.render("eventos.html", user = template_values, idEvento = idEvento2, titleEvento = titleEvento, fechaInicio = fechaI, fechaFin = fechaF, descrptionEvento = descrptionEvento)
            modificar = True
        if boton_eliminar == "Eliminar":
            if consulta is not None:
                global consulta
                contador = 0
                for i in consulta.evento:
                    if int(idEvento2) == i.idEvento:
                        consulta.evento.pop(contador)
                        consulta.put()
                        idEvento2 = 0
                        break
                    contador += 1
            lista = []
            global consulta
            for i in consulta.evento:
                lista.append(i)
            self.render("eventos.html",user = template_values, lista = lista)

class ContactosP(Handler):
    def get(self):
        global consulta
        global template_values
        global modificar
        lista = []
        for i in consulta.contacto:
            lista.append(i)
        self.render("contactos.html", user = template_values, lista = lista)
    def post(self):
        global consulta
        global idContacto
        global template_values
        global idContacto2
        global modificar
        name = self.request.get("name")
        phone = self.request.get("phone")
        fechaNacimiento = self.request.get("fechaNacimiento")
        address = self.request.get("address")
        email = self.request.get("email")
        if consulta is not None:
            contador = 0
            for i in consulta.contacto:
                idContacto = idContacto + 1
                if modificar == True:
                    if int(idContacto2) == i.idContacto:
                        consulta.contacto.pop(contador)
                        consulta.put()
                        idContacto2 = 0
                        modificar = False
                        break
                contador +=1
            nuevo_contacto = Contactos(idContacto = idContacto, name = name, phone = phone, fechaNacimiento = fechaNacimiento, address = address, email = email)
            consulta.contacto.append(nuevo_contacto)
            consulta.put()
            lista = []
            global consulta
            for i in consulta.contacto:
                lista.append(i)
            self.render("contactos.html", user = template_values, lista = lista)
class EditarContactos(Handler):
    def post(self):
        global consulta
        global template_values
        global idContacto2
        global modificar
        idContacto2 = self.request.get("idContacto_input")
        name = self.request.get("name_input")
        phone = self.request.get("phone_input")
        fechaNacimiento = self.request.get("fechaNacimiento_input")
        address = self.request.get("address_input")
        email = self.request.get("email_input")
        boton_modificar = self.request.get("modificar")
        boton_eliminar = self.request.get("eliminar")
        if boton_modificar == "Modificar":
            self.render("contactos.html", user = template_values, idContacto = idContacto2, name = name, phone = phone, fechaNacimiento = fechaNacimiento, address = address, email = email)
            modificar = True
        if boton_eliminar == "Eliminar":
            if consulta is not None:
                global consulta
                contador = 0
                for i in consulta.contacto:
                    if int(idContacto2) == i.idContacto:
                        consulta.contacto.pop(contador)
                        consulta.put()
                        idContacto2 = 0
                        break
                    contador += 1
            lista = []
            global consulta
            for i in consulta.contacto:
                lista.append(i)
            self.render("contactos.html", user = template_values, lista = lista)
class MenuP(Handler):
    def post(self):
        global template_values
        self.render("principal.html", user = template_values)


config = {}
config['webapp2_extras.sessions'] = {
    'secret_key': 'some-secret-key',
}


app = webapp2.WSGIApplication([('/', Login),
                               ('/click_login',Login),
                               ('/click_tareas',TareasP),
                               ('/click_registrarTarea',TareasP),
                               ('/click_salir',Logout),
                               ('/click_registro',Registro),
                               ('/click_modificar', EditarTarea),
                               ('/click_eventos', EventosP),
                               ('/click_modificarEv', EditarEventos),
                               ('/click_contactos', ContactosP),
                               ('/click_modificarCon', EditarContactos),
                               ('/click_menu', MenuP),
                               ('/click_logout', Logout)


], debug=True, config=config)
        