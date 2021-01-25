import sqlite3
import struct
import sys
import datetime

def usage():
    if len(sys.argv) !=2:
        print("[+]Missing file location!")
        print("[+]sample : \"python no3_CFBF inputfile\"")
        sys.exit()
def createDB():
    conn = sqlite3.connect("CFBFouput.db")
    cur = conn.cursor()
    conn.execute("CREATE TABLE parsed(Name TEXT PRIMARY KEY, object_Type TEXT, t_creation INTEGER, t_modified INTEGER, starting_sector_location TEXT,stream_size INTEGER)")
    conn.commit()
    cur.close()
    conn.close()    
def hd_sector_structure(hd):
    res={}
    res['Signature'] = hd[:0x8] 
    res['Hd_CLSID'] = hd[0x8:0x10] # class identifier
    res['Minor_version'] = hd[0x18:0x1a] #release version
    res['Major_version'] = hd[0x1a:0x1c] # file format version
    res['Byte_order'] = hd[0x1c:0x1e] # endian
    res['Sector_shift'] = hd[0x1e:0x20] # sector size
    res['Mini_sector_shift']=hd[0x20:0x22] # mini sector size
    res['Reserved']=hd[0x22:0x28] # reserved area
    res['Num_directory_sector']=hd[0x28:0x2c] # 3.x version not in use
    res['Num_FAT_sector']=hd[0x2c:0x30] # 파일 할당표에 할당된 섹터의 개수
    res['First_Directory_Location']=hd[0x30:0x34] # 디렉터리 개체의 시작 섹터 인덱스
    res['Transaction_Signature']=hd[0x34:0x38] #0값
    res['Mini_stream_cutoff']=hd[0x38:0x3c] # 표준 스트림 최소 크기
    res['First_Mini_FAT_location']=hd[0x3c:0x40] # 소형할당표 시작섹터 인덱스
    res['Num_mini_FAT']=hd[0x40:0x44] # 소형파일 할당표 할당섹터수
    res['First_DIFAT_location']=hd[0x44:0x48] # DIFAT 할당표의 시작인덱스
    res['Num_DIFAT']=hd[0x48:0x4c] # DIFAT에 할당된 섹터의 개수
    for i in range(struct.unpack('>i',res['Num_DIFAT'])[0]):
        res['DIFAT'+str(i)]=hd[0x4c+(i*4):0x50+(i*4)]
    return res
def directory_entry(hd):
    res={}
    res['Entry_Name']=str(struct.unpack('64s',hd[0x00:0x40])[0])[2:-1].replace('\\x00','')
    res['Name_len']=hd[0x40:0x42]
    res['Obj_type']=str(struct.unpack('c',hd[0x42:0x43])[0].hex())
    res['Color_flag']=hd[0x43:0x44]
    res['Left_Sibling_ID']=hd[0x44:0x48]
    res['Right_Sibling_ID']=hd[0x48:0x4C]
    res['Child_ID']=hd[0x4c:0x50]
    res['CLSID']=hd[0x50:0x60]
    res['State_bit']=hd[0x60:0x64]
    res['Creation_time']=int(struct.unpack('>2I',hd[0x64:0x6c])[1])
    res['Modified_time'] =int(struct.unpack('>2I',hd[0x6c:0x74])[1])
    res['Start_sector_location']=str(abs(struct.unpack('<I',hd[0x74:0x78])[0]))
    res['Stream_size']=str(abs(struct.unpack('<2I',hd[0x78:0x80])[0]))

    return res
def fileread():
    try :
        f = open(sys.argv[1],'rb')
    except:
        print("[+]File Read Error.")
        print("[+]")
        sys.exit()
    
    txt = f.read()
    tmp = txt[:496]
    hd_sector = hd_sector_structure(tmp)

    dir_entry = txt[0x1f400:]# 위치 찾아야함.
    
    dir_entry = directory_entry(dir_entry)
    

    #no1 : save in db : Name, Objtype, CreationTime,Modified time, starting sector location, streamsize
    conn=sqlite3.connect('CFBFouput.db')
    cur = conn.cursor()
    query = "INSERT INTO parsed VALUES('" 
    query += dir_entry['Entry_Name']+"','"
    query += dir_entry['Obj_type']+"','"
    query += str(datetime.datetime.fromtimestamp(dir_entry['Creation_time'])) +"','"
    query += str(datetime.datetime.fromtimestamp(dir_entry['Modified_time'])) +"','"
    query += dir_entry['Start_sector_location']+"','"
    query += dir_entry['Stream_size'] +"')"

    #cur.execute(query)
    conn.commit()


    f.close()

if __name__ =="__main__":
    createDB()
    usage()
    fileread() # 3-1