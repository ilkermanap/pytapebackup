import platform
import os
import hashlib
import sqlite3 as sql
sistem = platform.system().lower()

if sistem == "linux" or sistem == "linux2" or sistem == "darwin":
    SLASH = "/"
elif sistem == "windows":
    SLASH = "\\"

def find_hash(fname, blksize=65536):
    hasher = hashlib.sha256()
    with open(fname, "rb") as infile:
        buf = infile.read(blksize)
        while len(buf) > 0:
            hasher.update(buf)
            buf = infile.read(blksize)
    return hasher.hexdigest()
        
class MyFile:
    def __init__(self, path):
        self.name = path
        self.hashed_name = hashlib.sha224(self.name.encode("utf8")).hexdigest()
        self.stat = os.stat(self.name)
        # compressed size will be determined after compression.
        self.compressed_size = 0
        self.path = self.name[:self.name.rfind(SLASH)]
        self.hash_value = find_hash(self.name)


class MyDirectory:
    """
    Verilecek dizin icin, yedeklenmesi gereken dosyalari tespit eder.
    Verilmis ise, verilen tarihten sonra degisiklige ugramis olan dosyalari
    secer.

    blacklist uygulanacak uzantiara destek verilmeli.. mov, avi gibi dosyalari
    butun musteriler yedeklemek istemeyebilir..

    __init__(self, dizin, sontarih=None, karaliste=None, max_boy=10000000, 
             ayar=None, katalog=None,
             islem_zamani=None, islem_zamani_ts=None, 
             debug_kayitci=None):
    """

    def __init__(self, directory, lastdate=None, blacklist=None, max_size=10000000,
                 config=None, catalog=None,
                 date_processed=None, date_processed_ts=None):
        """
        :param dizin: yedeklemeye dahil edilecek olan dizin
        :param sontarih: Verilmis ise, degismis dosyalarin tespiti icin baz alinacak tarih
        :param karaliste: Yedege girmesi istenmeyen dosya uzantilari verilecek
        :return: katalog icin dosya yollari ve hashli halleri..
        """
        self.config = config
        self.catalog = catalog
        self.date_processed = date_processed
        self.date_processed_ts = date_processed_ts
        self.filenames = self.catalog.dosya_isimleri()
        if blacklist is None:
            blacklist = []
        self.directory = directory
        self.hashed = hashlib.sha224(self.directory.encode("utf8")).hexdigest()
        self.filelist = []
        self.full_backup = True
        lastdate = self.catalog.son_tarih()
        if lastdate is not None:
            self.full_backup = False
        self.max_size = max_size
        self.temp = "%s%s%s" % (self.config.yol, SLASH, self.date_processed)
        if not os.path.isdir(self.temp):
            os.makedirs(self.temp)

        self.tar_name = "%s%s%s" % (self.temp, SLASH, self.hashed)
        self.blacklist = []
        for extension in blacklist:
            self.blacklist.append(extension.lower())

        for dirName, subdirList, fileList in os.walk(self.directory, topdown=False):
            for fname in fileList:
                if (fname.split(".")[-1]).lower() not in self.blacklist:
                    proper = False
                    try:
                        x = os.stat('%s%s%s' % (dirName, SLASH, fname))
                        if x.st_size > 0:
                            proper = True
                        else:
                            proper = False
                    except:
                        proper = False

                    if proper:
                        if lastdate is None:
                            self.filelist.append(MyFile('%s%s%s' % (dirName, SLASH, fname)))
                        else:
                            fullname = '%s%s%s' % (dirName, SLASH, fname)
                            if fullname not in self.filenames:
                                self.filelist.append(MyFile('%s%s%s' % (dirName, SLASH, fname)))
                            else:
                                date_of_change = datetime.fromtimestamp(
                                    os.stat('%s%s%s' % (dirName, SLASH, fname)).st_mtime)
                                if date_of_change > lastdate:
                                    self.filelist.append(MyFile('%s%s%s' % (dirName, SLASH, fname)))
                    else:
                        # todo: if a file can't get into the list, we should report
                        print('%s%s%s file is not backed up.' % (dirName, SLASH, fname))
                        pass


    def update_time(self, newtime):
        self.date_processed, self.date_processed_ts = newtime
        
    def zaman_guncelle(self, yeni_zaman):
        self.date_processed, self.date_processed_ts = yeni_zaman

    #def dosya_listesi(self):
    def file_list_sqlite(self):
        """
        tum dosyalarin bilgisini tek seferde sqlite icine aktarmak icin..
        """
        temp = []
        for d in self.filelist:
            temp.append((self.date_processed_ts, d.directory, d.name, d.hashed_name, d.hash_value, d.stat.st_size, 0))
        return temp

    #def paket(self, sifreci, catalog, buyuk_katalog, sunucu,
    #          cihazno, yol, durum=None, dosyasil = False):
    def package(self, crypter, catalog, big_catalog, sunucu, cihazno, yol, remove_source=False):
        """
        Bu metod, bize o dizin icindeki dosyalarin adlari hash ile degistirilmis
        olanlarini iceren tar paketini olusturmali.
        :param cihazno:
        :type cihazno:
        :param sunucu:
        :param buyuk_katalog:
        :param katalog:
        :param sifreci:
        :return:
         """
        _size = 0
        eboyut = 0
        parts = 1

        fname = "%s-%06d.tar" % (self.tar_name, parts)

        tar = tarfile.open(fname, "w")
        for _file in self.filelist:
            _outfile  = "%s.enc" % _file.hashed_name
            crypter.encrypt(_file.name, _outfile , remove_source = remove_source)
            _filesize = os.stat(_outfile).st_size
            catalog.boy_guncelle(_file.name, _filesize)
            big_catalog.boy_guncelle(_file.name, _filesize)
            tar.add(_outfile)
            os.remove(_outfile)
            
            _size += _filesize
            if _size > self.max_size:
                eboyut = _size
                parts += 1                
                _size = 0
                tar.close()
                                    
                #sunucu.gonder(fname, self.date_processed, cihazno)
                # todo : move to backup location 
                
                fname = "%s-%06d.tar" % (self.tar_name, parts)
                tar = tarfile.open(fname, "w")

        if len(tar.getnames()) > 0:
            tar.close()
            # todo : move to backup location 
                        
#--------------------

class Backup:
    """
    [Generate backup for current directory]    
    """
    def __init__(self, config_dir_name):
        """Check config dir presence first
       
        Keyword arguments:  config dir name
        argument -- description
        """
        self.dir = os.path.realpath(os.path.curdir)
        self.config_dir = config_dir_name
        fullpath = os.path.abspath(self.config_dir)



class Database:
    def __init__(self, filename=None, schema=None):
        self._file = filename
        self.db = None
        if filename is None:
            self.db = sql.connect(":memory:", detect_types=sql.PARSE_DECLTYPES | sql.PARSE_COLNAMES)
            self._file = None
        else:
            self.db = sql.connect(self._file, detect_types=sql.PARSE_DECLTYPES | sql.PARSE_COLNAMES)

        if schema is not None:
            self.new_schema(schema)


    def connect(self):
        try:
            x = self.db.cursor()
            r = x.execute("SELECT 1 FROM dosyalar LIMIT 1").fetchall()
        except:
            if self._file is None:
                self.db = sql.connect(":memory:", detect_types=sql.PARSE_DECLTYPES | sql.PARSE_COLNAMES)
            else:
                self.db = sql.connect(self._file, detect_types=sql.PARSE_DECLTYPES | sql.PARSE_COLNAMES)

    def new_schema(self, schema):
        try:
            self.sorgu(schema)
        except:
            pass

    def query(self, _query):
        cr = self.db.cursor()
        cr.execute(_query)
        self.db.commit()

    def response(self, _query):
        cr = self.db.cursor()
        cr.execute(_query)
        return cr.fetchall()


class Catalogues:
    def __init__(self, path):
        self._files = glob.glob("%s%s*katalog" % (path, SLASH))

        self.dates = []
        for dt in self._files:
            self.dates.append(dt.split(SLASH)[-1])
        schema = "  "
        self.db = Database()

        # TODO tum kataloglarin tek vt altinda toplanmasi iyi olabilir.. icinde, hangi tarihlerin islenmis
        # oldugunu da tutariz.. boylece, islenmis tarihler yeniden girmez.
        # dosya ve dizinlere tarih te eklenir.. boylece tek vt uzerinde istedigimiz tarihe ait sorgu yapilir..
        # index unutma



class KatalogVT(Database):
    def __init__(self, _filename=None, _schema=None, date_processed_ts=None):
        Database.__init__(self, _filename=_filename, schema=_schema)
        self.date_processed_ts = islem_zamani_ts

    def dosya_getir(self, tarih, adi):
        cr = self.vt.cursor()
        cr.execute('SELECT max(tarih) , yeni_adi FROM dosyalar WHERE tarih < ? AND adi = ?', (tarih, adi))
        res = cr.fetchall()
        if len(res) == 0:
            return None
        else:
            return res[0]

    def dizin_getir(self, tarih, dizin):
        cr = self.vt.cursor()
        if dizin[-1] == SLASH:
            dizin = dizin[:-1]
        pboy = 0
        cr.execute(
            'SELECT max(tarih) , yeni_adi, paketli_boyu FROM dosyalar WHERE'
            ' tarih <= ? AND dizin  LIKE ?  GROUP BY adi ORDER BY tarih',
            (tarih, dizin + "%"))
        res = cr.fetchall()
        if len(res) == 0:
            return None
        else:
            temp = ""
            temp2 = {}
            for r in res:
                pboy += r[2]
                temp += ";".join(r[:-1]) + "|"
                temp2[r[1]] = r[0]
            return b64encode(bz2.compress(temp.encode("utf-8"))), temp2, pboy
        return None

    def dosyalar_ekle(self, dosyalar):
        cr = self.vt.cursor()
        self.debug_mesaj("katalog.py:dosyalar_ekle:%d adet dosya ekleniyor" % len(dosyalar))
        cr.executemany("INSERT INTO dosyalar VALUES(?, ?, ?, ?,? , ?, ?)", dosyalar)
        self.vt.commit()
        self.debug_mesaj("katalog.py:dosyalar_ekle:%d adet dosya eklendi" % len(dosyalar))

    def dosya_ekle(self, dosya):
        cr = self.vt.cursor()
        cr.execute("INSERT INTO dosyalar VALUES(?, ?, ?, ?,? , ?, ?)",
                   (self.islem_zamani_ts, dosya.dizin, dosya.adi, dosya.hashli_adi, dosya.hash_degeri,
                    dosya.stat.st_size, 0))
        self.vt.commit()

    def boy_guncelle(self, dosya_adi, paketli_boyu):
        cr = self.vt.cursor()
        cr.execute("UPDATE  dosyalar SET paketli_boyu = ? WHERE adi = ? ", (paketli_boyu, dosya_adi))
        self.vt.commit()

    def son_tarih(self, dizin=None):
        cr = self.vt.cursor()
        if dizin is None:
            cr.execute('SELECT max(tarih) AS "[timestamp]" FROM dosyalar')
        else:
            cr.execute('SELECT max(tarih) AS "[timestamp]" FROM dosyalar WHERE dizin=?', (dizin,))
        res = cr.fetchall()
        if len(res) == 0:
            return None
        else:
            return res[0][0]

    def gercek_adi(self, hashli):
        cr = self.vt.cursor()
        hashli = hashli.replace(".enc", "")
        cr.execute('SELECT adi FROM dosyalar WHERE yeni_adi= ?; ', (hashli,))
        c = cr.fetchall()
        return c[0][0]

    def kapasite(self):
        cr = self.vt.cursor()
        cr.execute('SELECT count(boyu), sum(boyu), sum(paketli_boyu) FROM dosyalar')
        c = cr.fetchall()
        return c[0]

    def vt_son_yedek(self, yedek_dizini=None):
        cr = self.vt.cursor()
        cr.execute('SELECT julianday() - julianday(max(tarih)) FROM dosyalar where dizin like "c:\\vtyedek\\%" ')
        c = cr.fetchall()
        if len(c) > 0:
            print(c[0])
            return c[0][0]
        else:
            return -1

    def dizinler(self):
        cr = self.vt.cursor()
        cr.execute("SELECT DISTINCT dizin FROM dosyalar ORDER BY dizin")
        return cr.fetchall()

    def tarihler(self, dizin=None):
        cr = self.vt.cursor()
        if dizin is None:
            cr.execute("SELECT DISTINCT tarih FROM dosyalar")
        else:
            cr.execute("SELECT DISTINCT tarih FROM dosyalar WHERE dizin LIKE ?", (dizin + "%",))
        return cr.fetchall()

    def versiyon(self, dosya):
        cr = self.vt.cursor()
        cr.execute("SELECT tarih FROM dosyalar WHERE adi = ?", (dosya,))
        return cr.fetchall()

    def dosya_varmi(self, dosya):
        cr = self.vt.cursor()
        cr.execute("SELECT count(adi) FROM dosyalar WHERE adi=?", (dosya,))
        if cr.fetchall()[0][0] > 0:
            return True
        else:
            return False

    def dosya_isimleri(self):
        cr = self.vt.cursor()
        cr.execute("SELECT DISTINCT adi FROM dosyalar")
        res = cr.fetchall()
        temp = []
        for f in res:
            temp.append(f[0])
        return temp

    def max_tarih(self):
        cr = self.vt.cursor()
        cr.execute('SELECT max(tarih) FROM dosyalar')
        c = cr.fetchall()
        if len(c) > 0:
            return c[0][0]
        else:
            return "Kayit yok"

    def dosyalar(self, toplam=False):
        cr = self.vt.cursor()
        cr.execute("SELECT DISTINCT adi, yeni_adi, boyu, paketli_boyu FROM dosyalar")
        return cr.fetchall()

    def birlestir(self, vt_dosyasi):
        # TODO   calistigi test edilmedi,  yeni dosyadaki kayitlar vt icinde varmi diye kontrol yok..
        # kontrol kismini dusunup eklemek gerek
        sorgu = """attach '%s' as toMerge;
BEGIN;
insert into dosyalar select * from  toMerge.dosyalar;
COMMIT;
detach toMerge """ % vt_dosyasi

        self.vt.executescript(sorgu)
        self.vt.commit()
