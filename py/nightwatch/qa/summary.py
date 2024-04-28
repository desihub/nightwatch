from desiutil.log import get_logger

import os
import fitsio
from datetime import datetime
import sqlite3

try:
    import psycopg2
    import common_postgres as copo
    has_postgres = True
except ImportError as e:
    log = get_logger()
    log.warning(e)
    has_postgres = False


class Singleton(type):
    """Basic singleton type. Use this to enable multiple DB formats.
    """
    _instances = {}
    def __call__(cls, *args, **kwargs):
        if cls not in cls._instances:
            cls._instances[cls] = super(Singleton, cls).__call__(*args, **kwargs)
        return cls._instances[cls]


class SummaryDB(metaclass=Singleton):
    """QA summary DB base type.
    """

    programs_flats = {
        'CALIB DESI-CALIB-00 LEDs only',
        'CALIB DESI-CALIB-01 LEDs only',
        'CALIB DESI-CALIB-02 LEDs only',
        'CALIB DESI-CALIB-03 LEDs only',
        'LED03 flat for CTE check',
    }

    programs_arcs_short = {
        'CALIB short Arcs all'
    }

    programs_arcs_long = {
        'CALIB long Arcs Cd+Xe',
    }

    programs_other = {
		'CALIB ZEROs for nightly bias',
		'CALIB Dark 5min',
		'ZEROs for dark sequence C',
		'DARK 1200.0s for dark sequence C',
		'BRIGHT',
		'DARK',
		'ZEROs for morning darks',
		'Morning darks',
		'ZEROs to stabilize CCDs',
        'spec_tests',
    }

    obstypes = {
        'DARK',
        'ZERO',
        'SCIENCE',
        'FLAT',
        'ARC',
        'OTHER'
    }

    programs_all = programs_other | programs_arcs_short | programs_arcs_long | programs_flats

    def qa_header_to_dict(self, fitshdr, use_datetime=False):
        """Pack QA exposure FITS header into a dictionary.

        Parameters
        ----------
        fitshdr : fitsio.header.FITSHDR
            FITS header written by DOS.
        use_datetime : bool
            If true, save time as DATETIME; else convert to INT.

        Returns
        -------
        hdr : dict
            Dictionary used to pack exposure data into DB.
        """
        expid = fitshdr['EXPID']
        night = fitshdr['NIGHT']
        program = fitshdr['PROGRAM']
        obstype = fitshdr['OBSTYPE']
        if use_datetime:
            time = fitshdr['DATE-OBS'].split('.')[0].replace('T', ' ')
        else:
            time = datetime.strptime(fitshdr['DATE-OBS'].split('.')[0], '%Y-%m-%dT%H:%M:%S').timestamp()

        hdr = {
            'expid'   : expid,
            'night'   : night,
            'obstype' : obstype,
            'program' : program,
            'time'    : int(time)
        }

        return hdr

    def qa_peramp_to_str(self, peramp_data):
        """Pack QA PER_AMP table data into a simple string.

        Parameters
        ----------
        peramp_data : ndarray
            Data array from FITS.

        Returns
        -------
        data : str
            Output string of values for insertion into SQL.
        """
        data = []
        for row in peramp_data:
            data.append("({1}, {2}, '{3}', '{4}', {5}, {6}, {7} )".format(*row))
        return ','.join(data)

    def qa_percamera_to_str(self, percamera_data):
        """Pack QA PER_CAMERA table data into a simple string.

        Parameters
        ----------
        percamera_data : ndarray
            Data array from FITS.

        Returns
        -------
        data : str
            Output string of values for insertion into SQL.
        """
        data = []
        for row in percamera_data:
            data.append("({1}, {2}, '{3}', {4}, {5}, {6}, {7}, {8}, {9})".format(*row))
        return ','.join(data)

    def qa_percamera_sig_to_str(self, percamera_sig_data):
        """Pack QA PER_CAMERA uncertainty data into a simple string.

        Parameters
        ----------
        percamera_sig_data : ndarray
            Data array from FITS.

        Returns
        -------
        data : str
            Output string of values for insertion into SQL.
        """
        data = []
        for row in percamera_sig_data:
            data.append("({1}, {2}, '{3}', {10}, {11}, {12}, {13}, {14}, {15})".format(*row))
        return ','.join(data)

    def qa_perspectro_to_str(self, perspectro_data):
        """Pack QA PER_CAMERA table data into a simple string.

        Parameters
        ----------
        perspectro_data : ndarray
            Data array from FITS.

        Returns
        -------
        data : str
            Output string of values for insertion into SQL.
        """
        data = []
        for row in perspectro_data:
            row = list(row)
            dastring = ','.join([str(d) for d in row[4:]])
            data.append("({}, '{}', {})".format(row[1], row[3], dastring))
        return ','.join(data)

    def create_tables(self):
        pass

    def write_exposure_to_db(fitsfile):
        pass


class SQLiteSummaryDB(SummaryDB):
    """Summary QA DB in SQLite.
    """

    table_commands = {
        
        # Header creation command.
        'nw_header' : """CREATE TABLE nw_header(
            expid INT NOT NULL,
            night INT NOT NULL,
            obstype VARCHAR(20) NOT NULL,
            program VARCHAR(100) NOT NULL,
            time INT NOT NULL,
            PRIMARY KEY(expid));""",

        'nw_header_idx' : """CREATE INDEX expid_index ON nw_header(expid);""",
        
        # peramp table creation command.
        'nw_peramp' : """CREATE TABLE nw_peramp(
            expid INT NOT NULL,
            spectro TINYINT NOT NULL,
            cam CHAR NOT NULL,
            amp CHAR NOT NULL,
            readnoise FLOAT,
            bias FLOAT,
            cosmic_rate FLOAT);""",
        
        # percamera table creation command.
        'nw_percamera' : """CREATE TABLE nw_percamera(
            expid INT NOT NULL,
            spectro TINYINT NOT NULL,
            cam CHAR NOT NULL,
            meandx FLOAT,
            mindx FLOAT,
            maxdx FLOAT,
            meandy FLOAT,
            mindy FLOAT,
            maxdy FLOAT,
            PRIMARY KEY(expid, spectro, cam));""",
        
        # percamera sigma table creation command.
        'nw_percamera_sig' : """CREATE TABLE nw_percamera_sig(
            expid INT NOT NULL,
            spectro TINYINT NOT NULL,
            cam CHAR NOT NULL,
            meanxsig FLOAT,
            minxsig FLOAT,
            maxxsig FLOAT,
            meanysig FLOAT,
            minysig FLOAT,
            maxysig FLOAT,
            PRIMARY KEY(expid, spectro, cam));""",
        
        # flux values from calibration data: flats (LEDs)
        'nw_perspectro_flats' : """CREATE TABLE nw_perspectro_flats(
            expid INT NOT NULL,
            spectro TINYINT NOT NULL,
            b_integ_flux FLOAT,
            r_integ_flux FLOAT,
            z_integ_flux FLOAT,
            PRIMARY KEY(expid, spectro));""",
        
        # flux values from calibration data: short arcs 
        'nw_perspectro_short_arcs' : """CREATE TABLE nw_perspectro_short_arcs(
            expid INT NOT NULL,
            spectro TINYINT NOT NULL,
            B4048 FLOAT,
            B4679 FLOAT,
            B4801 FLOAT,
            B5087 FLOAT,
            B5462 FLOAT,
            R6145 FLOAT,
            R6385 FLOAT,
            R6404 FLOAT,
            R6508 FLOAT,
            R6680 FLOAT,
            R6931 FLOAT,
            R7034 FLOAT,
            R7247 FLOAT,
            Z7604 FLOAT,
            Z8115 FLOAT,
            Z8192 FLOAT,
            Z8266 FLOAT,
            Z8301 FLOAT,
            Z8779 FLOAT,
            Z8822 FLOAT,
            Z8931 FLOAT,
            PRIMARY KEY(expid, spectro));""",
        
        # flux values from calibration data: long arcs 
        'nw_perspectro_long_arcs' : """CREATE TABLE nw_perspectro_long_arcs(
            expid INT NOT NULL,
            spectro TINYINT NOT NULL,
            B3612 FLOAT,                          
            B4679 FLOAT,                          
            B4801 FLOAT,                          
            B5087 FLOAT,                          
            R6440 FLOAT,                          
            Z8234 FLOAT,                          
            Z8283 FLOAT,                          
            Z8822 FLOAT,                          
            Z8955 FLOAT,                          
            Z9048 FLOAT,                          
            Z9165 FLOAT,                          
            Z9802 FLOAT,
            PRIMARY KEY(expid, spectro));""",
    }

    def __init__(self, dbfile, updates=False):
        """Initialize with dbfile.

        dbfile : str
            Path to SQLite database.
        updates : bool
            Default behavior is write-once. If true, allow updates to entries.
        """
        self.dbfile = dbfile
        newdb = not os.path.isfile(self.dbfile)
        self.dbconn = self.get_db_connection(self.dbfile)
        self.updates = updates

        if newdb:
            log = get_logger()
            log.info(f'Creating new DB: {self.dbfile}')
            self.create_tables()

    def get_db_connection(self, dbfilename):
        """Connect to the SQLite database.

        Parameters
        ----------
        dbfilename : str
            Path to the database.

        Returns
        -------
        db_con : sqlite3.Connection
            Connection to the SQLite database file.
        """
        db_con = sqlite3.connect(dbfilename)
        return db_con

    def create_tables(self):
        """Set up tables during instantiation of the database.
        """
        log = get_logger()
        db_cur = self.dbconn.cursor()

        try:
            for tab, tab_cmd in self.table_commands.items():
                log.info(tab_cmd)
                db_cur.execute(tab_cmd)
        finally:
            db_cur.close()

        self.dbconn.commit()

    def insert_exposure_data(self, header, data_dict):
        """Insert data into database.

        Parameters
        ----------
        header : dict
            Dictionary of header info to write to the DB.
        data_dict :
            Dictionary of data tables to write to the DB.

        Returns
        -------
        status : bool
            True if exposure data were written, false otherwise.
        """
        log = get_logger()
        db_cur = self.dbconn.cursor()

        try:
            # Check if current exposure is in the DB.
            result = db_cur.execute(f'SELECT expid FROM nw_header WHERE expid={header["expid"]}').fetchall()

            if len(result) == 0:
                # Insert the exposure header.
                insert_cmd = "INSERT INTO nw_header VALUES ({expid}, {night}, \"{obstype}\", \"{program}\", {time})".format(**header)
                print(insert_cmd)
                db_cur.execute(insert_cmd)

                # Insert all exposure data.
                for tab, data in data_dict.items():
                    insert_cmd = f'INSERT INTO {tab} VALUES {data}'
                    print(insert_cmd)
                    db_cur.execute(insert_cmd)
            else:
                if self.updates:
                    return True
                else:
                    log.warning(f'expid {header["expid"]} already exists in DB.')
                    return False
        finally:
            db_cur.close()

        self.dbconn.commit()

        return True

    def write_exposure_to_db(self, fitsfile):
        """Read FITS data and add a DB entry.

        Parameters
        ----------
        fitsfile : str
            Input FITS data.
        """
        log = get_logger()

        try:
            # Extract exposure header.
            fitshdr = fitsio.read_header(fitsfile)
            hdict = self.qa_header_to_dict(fitshdr, use_datetime=False)
            qadict = {}

            # Extract QA data to a dictionary.
            ff = fitsio.FITS(fitsfile)

            if 'PER_AMP' in ff:
                data = ff['PER_AMP'].read()
                qadict['nw_peramp'] = self.qa_peramp_to_str(data)

            if 'PER_CAMERA' in ff:
                data = ff['PER_CAMERA'].read()
                qadict['nw_percamera'] = self.qa_percamera_to_str(data)

                if len(data.dtype) == 16:
                    qadict['nw_percamera_sig'] = self.qa_percamera_sig_to_str(data)
            
            if 'PER_SPECTRO' in ff:
                data = ff['PER_SPECTRO'].read()
                prog = fitshdr['PROGRAM']

                if prog in self.programs_arcs_short:
                    qadict['nw_perspectro_short_arcs'] = self.qa_perspectro_to_str(data)
                elif prog in self.programs_arcs_long:
                    qadict['nw_perspectro_long_arcs'] = self.qa_perspectro_to_str(data)
                elif prog in self.programs_flats:
                    qadict['nw_perspectro_flats'] = self.qa_perspectro_to_str(data)
                else:
                    log.warn(f'Will not write PROGRAM {prog} to DB.')

            # Write header and data for exposure to the DB.
            self.insert_exposure_data(hdict, qadict)

        except Exception as e:
            log.error(e)

