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

class Cuentas(ndb.Model):
    username = ndb.StringProperty()
    password = ndb.StringProperty()

class Tareas(ndb.Model):
    tarea = ndb.StringProperty()
    nota = ndb.StringProperty()

class Login(Handler):
    def get(self):
        self.render("index.html")
    def post(self):
        global template_values
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
        self.render("tareas.html")
    def post(self):
        tarea = self.request.get('nombreTarea')
        nota = self.request.get('nota')
        consulta = Tareas.query(ndb.AND(Tareas.tarea==tarea, Tareas.nota==nota)).get()
        if consulta is not None:
            consulta.tarea = tarea
            consulta.nota = nota
            consulta.put()
            tarea = ''
            nota = ''
        self.redirect("/")


        
            
config = {}
config['webapp2_extras.sessions'] = {
    'secret_key': 'some-secret-key',
}


app = webapp2.WSGIApplication([('/', Login),
                               ('/click_login',Login),
                               ('/click_tareas',TareasP),
                               ('/click_registrarTarea',TareasP),
                               ('/click_salir',Logout),
                               ('/click_registro',Registro)

], debug=True, config=config)
        