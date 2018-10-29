import os
import uuid
import model
from sqlalchemy import create_engine                           
from sqlalchemy.exc import ProgrammingError                    
from sqlalchemy.orm import sessionmaker, scoped_session 
from datetime import datetime

if 'RDS_HOSTNAME' in os.environ:
    DATABASE_NAME = os.environ['RDS_DB_NAME']
    USERNAME = os.environ['RDS_USERNAME']
    PASSWORD = os.environ['RDS_PASSWORD']
    HOSTNAME =  os.environ['RDS_HOSTNAME']
    PORT = os.environ['RDS_PORT']
else:
    HOSTNAME = 'storeobjectapp.cxf6ynbp3h8k.us-west-2.rds.amazonaws.com'
    DATABASE_NAME = 'storeobjectapp'
    USERNAME = 'master'
    PASSWORD = 'Testing1234'
    PORT = 5432


class DatabaseError(Exception):
    """ This will raised when there is any db related error """

class RDSPostgresDb(object):
    """ 
    """
  
    def __init__(self, hostname=HOSTNAME, port=PORT,
                 username=USERNAME, password=PASSWORD,
                 database=DATABASE_NAME):
        self.host = hostname
        self.port = port
        self.username = username
        self.password = password
        self.database = database
        root_connection_string = ("postgresql://{host}:{port}/"
                                    "{database}?"
                                    "user={username}&"
                                    "password={password}").format(
              host=self.host, port=self.port, database=self.database,
              username=self.username, password=self.password)
  
        connection_string = ("postgresql://{host}:{port}/{database}?"
                               "user={username}&password={password}").format(
              host=self.host, port=self.port, database=self.database,
              username=self.username, password=self.password)
  
        root_engine = create_engine(root_connection_string)
        self.root_session = sessionmaker(bind=root_engine)()
        self._engine = create_engine(connection_string, pool_recycle=3600)
        self.session_factory = sessionmaker(bind=self._engine)
        self.scoped_session = scoped_session(self.session_factory)
  
    @property
    def engine(self):
        return self._engine
  
    def open(self):
        return self.session_factory()
  
    def get_factory(self):
        return self.session_factory
  
    def get_session(self):
        return self.scoped_session
  
    def create(self):
        try:
            self.root_session.connection().connection.set_isolation_level(0)
            self.root_session.execute("CREATE DATABASE {0}".format(
                  self.database_name))
            self.root_session.connection().connection.set_isolation_level(0)
        except ProgrammingError as err:
            if "already exists" not in err.orig:
                pass
  
            Base.metadata.create_all(self._engine)
  
    def drop(self):
        Base.metadata.drop_all(self._engine)
        self._engine.dispose()

        self.root_session.connection().connection.set_isolation_level(0)
        self.root_session.execute("DROP DATABASE {0}".format(
            self.database_name))
        self.root_session.connection().connection.set_isolation_level(0)

def create_all_tables(db_engine):
    model.Base.metadata.create_all(db_engine)

def upsert(dbs, table_obj, record):
  
    try:
        dbs.execute(table_obj.__table__.insert(), record)
    except IntegrityError as ierr:
        dbs.rollback()
        dbs.merge(table_obj(**record))
    except OperationalError as operr:
              raise
    finally:
        dbs.commit()

if __name__ == '__main__':
    pg_client = RDSPostgresDb()
    db_session = pg_client.get_session()
    db_engine = pg_client.engine
    create_all_tables(db_engine)
      
    # Upsert/Insert row into table
    user_record = dict(uuid=str(uuid.uuid4()),
                        username='viswa',
                        firstname='viswa',
                        lastname='kambam',
                        password='password',
                        email='kambam@gmail.com',
                        created_date=datetime.now(),
                        bucket='{}-{}'.format('viswa', str(uuid.uuid4())[:8]))
    upsert(db_session, model.UserInfo, user_record)

    # delete
    #db_session.execute(model.FileInfo.__table__.delete().where(model.FileInfo.owner=='bc17582c-84b9-4afd-bacd-bcbfe7be3eb1'))
    #db_session.commit()

    #select
    #res = db_session.execute(model.UserInfo.__table__.select().where(model.UserInfo.email=='kathir@gmail.com'))
    #print res.fetchall()[0][3]

