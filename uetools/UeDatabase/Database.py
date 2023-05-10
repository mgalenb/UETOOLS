from uetools import Case

class Database():
    # NOTE For some reason, it takes forever to create/restore Database 
    # whenever polycollections are included. The pickle size is only
    # 26M, no reason for the long runtime...
    def __init__(self, database, savedbname=None, dbidentifier='_UeDB', 
        sortvar='ne', sortlocation='midplane', rerun=False):
        from os import getcwd
        from os.path import isfile, isdir
        self.cwd = getcwd()
        self.cases = {}
        self.dbidentifier = dbidentifier
        self.datbasename = database
        self.sortvar = sortvar
        self.rerun = rerun
        self.sortlocation = sortlocation
        self.create_database(database)
        # TODO: Store commonly used grid locations
        # TODO: Account for different grids
        self.ixmp = self.get('ixmp')[0]
        self.iysptrx = self.get('iysptrx')[0]

        # Make sort location more advanced
        if self.sortlocation == 'midplane':
            self.sortlocation = (self.ixmp, self.iysptrx+1)
        elif isinstance(self.sortlocation, str):
            print('Sort location option "{}" not recognized. Aborting'.format(\
                self.sortlocation))
        # Sort here
        self.sort(sortvar, self.sortlocation)

        # Save if requested
        if savedbname is not None:
            self.save(savedbname)
            

    def top(self):
        self.chdir(self.cwd)

    def chdir(self, path):
        from os import chdir
        chdir(path)

    def is_case(self, file):
        from h5py import File
        try:
            f = File(file, 'r')
            ret = True
            # Check that necessary groups are present in file
            for entry in ['centered', 'staggered', 'restore', 'grid', 'setup']:
                if entry not in f.keys():
                    ret = False
            f.close()
            return ret
        except:
            return False

    def save(self, savename):
        """ Save the database """
        from pickle import dump
        with open('{}.db'.format(savename.split('.')[0]), 'wb') as f:
            dump(self, f)
    

    def sort(self, variable, location, increasing = True):
        """ Sorts cases according to variable at location """
        from numpy import argsort, where
        order = argsort(self.get(self.sortvar)[:, location[0], location[1]])
        neworder = {}
        for i in order:
            key = list(self.cases.keys())[i]
            neworder[key] = self.cases[key]
        self.cases = neworder

        self.scanvar = self.get(self.sortvar)[:, self.sortlocation[0], 
            self.sortlocation[1]]
        

    def create_database(self, path):
        from os import walk
        from os.path import abspath
        from tqdm import tqdm
        path = abspath(path)
        self.chdir(path)
        createdb = []
        for parent, dirs, files in walk('.'):
            subdir = parent.split('/')[-1]
            databases = [db for db in files if self.is_case('{}/{}'.format(\
                parent, db))]
            if self.rerun is False:
                # HDF5s identified
                if len(databases) == 1:
                    # Verify all necessary data is present
                    self.cases['{}/{}'.format(subdir, databases[0].replace(\
                        '.hdf5', ''))] = Case('{}/{}'.format(parent, 
                        databases[0]), inplace=True, verbose=False, 
                        database=True)
                elif len(databases) > 1:
                    for db in databases:
                        self.cases['{}/{}'.format(subdir, db.replace('.hdf5', 
                        ''))] = Case('{}/{}'.format(parent, db), inplace=True,
                        database=True)
                # No database found, store location where input is
                # Changing dirs while executing walk breaks the call
                elif 'input.yaml' in files:
                    createdb.append(parent)
            else:
                if 'input.yaml' in files:
                    createdb.append(parent)
        # Now, create and read the files
        if len(createdb)>0:
            print('===== CREATING NEW CASE DUMPS =====')
            for newdbfolder in tqdm(createdb):
                subdir = newdbfolder.split('/')[-1]
                self.chdir(path)
                self.chdir(newdbfolder)
                Case('input.yaml', verbose=False).save('{}{}.hdf5'\
                    .format(subdir, self.dbidentifier))
                self.cases['{}/{}'.format(subdir, '{}{}'.format(subdir, 
                    self.dbidentifier))] = Case('{}{}.hdf5'.format(subdir, 
                    self.dbidentifier), inplace=True, verbose=False)
                self.chdir(path)
        self.top() 

    def get(self, var, **kwargs):
        """ Returns an array of var for all cases """
        # TODO: Supress verbose output
        from numpy import array
        ret = []
        for key, case in self.cases.items():
            ret.append(case.get(var, **kwargs))
        return array(ret)


    def plotIT(self, var, **kwargs):
        return self.plotscan(var, (1, self.iysptrx+1), **kwargs) 

    def plotOT(self, var, **kwargs):
        return self.plotscan(var, (-2, self.iysptrx+1), **kwargs) 

    def plotOMP(self, var, **kwargs):
        return self.plotscan(var, (self.ixmp, self.iysptrx+1), **kwargs) 

    def plotscan(self, var, location, **kwargs):
        return self.plotvar(self.scanvar, var[:, location[0], location[1]], 
            **kwargs)

    def plotvar(self, xvar, yvar, ax=None, **kwargs):
        """ Plots yvar as a function of xvar for all cases """
        from matplotlib.pyplot import subplots
        if ax is None:
            f, ax = subplots()

        try:
            kwargs['marker']
        except:
            kwargs['marker']='.'
        try:
            kwargs['linestyle']
        except:
            kwargs['linestyle']=''
        try:
            kwargs['color']
        except:
            kwargs['color']='k'

        ax.plot(xvar, yvar, **kwargs)

        return ax.get_figure() 

    
    def plot_series(self):
        """ Returns a series of figures to scroll through """
        print('TBD')
    
    def animation(self):
        """ Creates an animation from a series of figures """ 
        print('TBD')


def restoredb(restorename):
    """ Restore a database """
    from pickle import load
    with open(restorename, 'rb') as f:
        db = load(f)
    return db
