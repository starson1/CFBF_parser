import sqlite3
import struct
import sys
import datetime

def usage():
    if len(sys.argv) !=3:
        print("[+]Wrong Input!")
        print("[+]sample : \"python no3_CFBF.py @input_file @output_db_name\"")
        sys.exit()
def createDB():
    try:
        conn = sqlite3.connect(sys.argv[2])
    except:
        print("[+]DB name Error.")
        sys.exit()
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
    res['SECID']=hd[0x30:0x34] # 디렉터리 개체의 시작 섹터 인덱스
    res['Transaction_Signature']=hd[0x34:0x38] #0값
    res['Mini_stream_cutoff']=hd[0x38:0x3c] # 표준 스트림 최소 크기
    res['First_Mini_FAT_location']=hd[0x3c:0x40] # 소형할당표 시작섹터 인덱스
    res['Num_mini_FAT']=hd[0x40:0x44] # 소형파일 할당표 할당섹터수
    res['First_DIFAT_location']=hd[0x44:0x48] # DIFAT 할당표의 시작인덱스
    res['Num_DIFAT']=hd[0x48:0x4c] # DIFAT에 할당된 섹터의 개수
    for i in range(struct.unpack('<i',res['Num_FAT_sector'])[0]):
        res['DIFAT'+str(i)]=hd[0x4c+(i*4):0x50+(i*4)]
    
    return res
def directory_entry(hd):
    res={}
    res['Entry_Name']=str(struct.unpack('64s',hd[0x00:0x40])[0])[2:-1].replace('\\x00','') #Name
    res['Name_len']=struct.unpack('H',hd[0x40:0x42])[0] #Length
    res['Obj_type']=str(struct.unpack('c',hd[0x42:0x43])[0].hex())#Type
    res['Color_flag']=hd[0x43:0x44] #ColorFlag
    res['Left_Sibling_ID']=hd[0x44:0x48]#Left ID
    res['Right_Sibling_ID']=hd[0x48:0x4C] #Right ID
    res['Child_ID']=hd[0x4c:0x50]# Child ID
    res['CLSID']=hd[0x50:0x60] # CLSID
    res['State_bit']=hd[0x60:0x64]# State
    res['Creation_time']=int(struct.unpack('>2I',hd[0x64:0x6c])[1])#CreateTIme
    res['Modified_time'] =int(struct.unpack('>2I',hd[0x6c:0x74])[1])#ModifyTime
    res['Start_sector_location']=str(abs(struct.unpack('<I',hd[0x74:0x78])[0]))#SecID
    res['Stream_size']=str(abs(struct.unpack('<2I',hd[0x78:0x80])[0]))#Size
    return res
def insertDB(entryname, objtype,createtime,modifitime,startsecloc,streamsize):
    try:
        conn=sqlite3.connect(sys.argv[2])
    except:
        print("[+]DB name Error.")
        sys.exit()
    cur = conn.cursor()

    query = "INSERT INTO parsed VALUES('" 
    query += entryname+"','"
    query += objtype+"','"
    query += createtime +"','"
    query += modifitime +"','"
    query += startsecloc+"','"
    query += streamsize +"')"

    cur.execute(query)
    conn.commit()
def fileread():
    try :
        f = open(sys.argv[1],'rb')
    except:
        print("[+]File Read Error.")
        sys.exit()
    
    txt = f.read()
    tmp = txt[:496] # file sturcture
    hd_sector = hd_sector_structure(tmp)
    
    DirLoc=int(struct.unpack('<I',hd_sector['SECID'])[0])+1
    sec_size = pow(2,int(struct.unpack('<H',hd_sector['Sector_shift'])[0]))
    numFAT = int(struct.unpack('<I',hd_sector['Num_FAT_sector'])[0])
    for i in range(0,4*numFAT):
        dir_entry = txt[DirLoc*sec_size+(0x80*i):DirLoc*sec_size+(0x80*(i+1))]
        ent_dic = directory_entry(dir_entry)
        insertDB(str(ent_dic['Entry_Name']),str(ent_dic['Obj_type']),str(ent_dic['Creation_time']),str(ent_dic['Modified_time']),str(ent_dic['Start_sector_location']),str(ent_dic['Stream_size']))
    f.close()
def Root_data():
    try :
        f = open(sys.argv[1],'rb')
    except:
        print("[+]File Read Error.")
        sys.exit()
    
    txt = f.read()
    tmp = txt[:496]
    f.close()
    hd_sector = hd_sector_structure(tmp)
    
    DirLoc=int(struct.unpack('<I',hd_sector['SECID'])[0])+1
    sec_size = pow(2,int(struct.unpack('<H',hd_sector['Sector_shift'])[0]))
    numFAT = int(struct.unpack('<I',hd_sector['Num_FAT_sector'])[0])
    dir_entry = txt[DirLoc*sec_size+0X80:DirLoc*sec_size+0x100]
    ent_dic = directory_entry(dir_entry)

    #Root entry Data stream
    stream_loc = (sec_size * (int(ent_dic['Start_sector_location'])+1))
    stream_len = int(ent_dic['Stream_size'])
    data = str(struct.unpack(str(stream_len)+'s',txt[stream_loc:stream_loc+stream_len])[0])[2:-1]
    of=open("../Root_Entry_Stream_Data.txt",'w')
    of.write(data)
    of.close()
    
def CombObj_data():
    try :
        f = open(sys.argv[1],'rb')
    except:
        print("[+]File Read Error.")
        sys.exit()
    
    txt = f.read()
    tmp = txt[:496]
    f.close()
    hd_sector = hd_sector_structure(tmp)

    DirLoc=int(struct.unpack('<I',hd_sector['SECID'])[0])+1
    sec_size = pow(2,int(struct.unpack('<H',hd_sector['Sector_shift'])[0]))
    numFAT = int(struct.unpack('<I',hd_sector['Num_FAT_sector'])[0])
    dir_entry = txt[DirLoc*sec_size:DirLoc*sec_size+0x80]
    ent_dic = directory_entry(dir_entry)
    
    #Compobj entry stream
    stream_loc = (sec_size * (int(ent_dic['Start_sector_location'])+1))
    stream_len = int(ent_dic['Stream_size'])
    data = str(struct.unpack(str(stream_len)+'s',txt[stream_loc:stream_loc+stream_len])[0])[2:-1]
    of=open("../Compbj_Entry_Stream_Data.txt",'w')
    of.write(data)
    of.close()

if __name__ =="__main__":
    createDB()
    usage()
    fileread() # 3-1
    Root_data()
    CombObj_data() # 3-3
     