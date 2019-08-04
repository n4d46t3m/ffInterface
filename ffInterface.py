'''
ffInterface v1.2
  __  __ ___       _             __ 
 / _|/ _|_ _|_ __ | |_ ___ _ __ / _| __ _  ___ ___ 
| |_| |_ | || '_ \| __/ ._\ '__| |_ / _` |/  _/ ._\
|_| |_| |___|_| |_|\__\___|_|  |_|  \__,_|\___\___|

Rielabora le info di ffprobe per generare comandi ffmpeg secondo presets
Si poteva usare solo Bash? Si

0) In questa versione il tutto è fatto come uno script procedurale, dalla 1.3 
è adottato un metodo ad oggetti. Questa versione 1.2 è da considerare come un 
caso di test / studio. Per poter usare facilmente ffInterface in altri progetti
usare versioni >= 1.3
1) Ora viene considerato solo lo stream 0 ed i suoi substreams 
che sono per proprietà traansitiva intesi come streams, per il futuro
fare in modo che vengano trattati tutti gli stream padre se esistenti 
e non solo lo 0, di conseguenza, ogni stream padre avrà N substreams
2) Ci sono problemi se il file non ha tracce sottotoli o se non ci sono 
sub di default.. (PROBABILMENTE RISOLTO)

Testato con ffprobe e ffmpeg 3.4.4

Questo codice è brutale e probabilmente non è pythonista.
Don't try this at home.
'''

import subprocess
import io
import os
import sys, getopt

swName = os.path.basename(__file__)
swVersion = '1.2'

fileMovie = ''
outputFile = ''
defaultPreset = 'dvdFilmItaH264CopyRestMkv'
preset = ''
prefix = 'n4d46t3m'
stripMeta = False
verboseMode = False

def checkInputFile(fileMovie):
    if(not os.path.isfile(fileMovie)):
        raise ValueError("File di input non trovato")
    else:
        return True

def printPresets():
    print('''
    Preset disponibili:
    \tdvdFilmItaH264CopyRestMkv
    \tdvdFilmItaCopyAllMkv
    \tdvdExtraItaH264CopyRestMkv
    \tdvdExtraItaCopyAllMkv''')

def printHelp():
    print()
    print(swName + ' v' + swVersion, end='')
    print("""
              __  __ ___       _             __ 
             / _|/ _|_ _|_ __ | |_ ___ _ __ / _| __ _  ___ ___ 
            | |_| |_ | || '_ \| __/ ._\ '__| |_ / _` |/  _/ ._\\
            |_| |_| |___|_| |_|\__\___|_|  |_|  \__,_|\___\___|
            """, end='')
    print()
    print('USAGE:')
    print('\tpython3 ' + __file__ + ' -i <inputFile> [-d] [-p <presetName>] [-s] [-o <outputFile>] [-h] [-v]')
    print()
    print('-i, --input <inputFile>')
    print('''
    Il nome del file da comprimere con l'intero path nel caso in cui non si trovi 
    nella stessa directory dello script (Parametro Obbligatorio)''')
    print()
    print('-s, --stripmeta')
    print('''
    Elimina tutti i metadata non ufficiali ffmpeg, potrebbe eliminare anche informazioni 
    legate al nome della lingua di uno stream, infatti, il comando per la compressione prodotto da 
    questo script contiene anche una parte per cercare di reimpostare almeno metadata base quali 
    appunto informazioni sul nome della lingua di uno stream''')
    print()
    print('-o, -output <outputFile>')
    print('''
    Se non è specificato verrà prodotto nella directory dell'input un file avente lo stesso nome del
    file di input ma con l'estensione specificata nel preset ed un prefisso.
    Se specificato, il file di output verrà salvato con il nome scelto (si possono inserire anche 
    path per impostare una directory di destinazione diversa da quella del file di input)
    ''')
    print()
    print('-p, --preset <presetName>')
    printPresets()
    print('''
    I preset disponibili sono facilmente comprensibili, i loro nomi sono in camel case e 
    sono pensati per seguire la stessa logica:\n
    \tSe un preset inizia con dvdFilm seguito dalla lingua, verranno mantenute tutte le tracce audio
    \te sottotitoli ma se presente, verrà impostata come traccia audio di default la traccia specificata 
    \tnel nome del preset, quindi per dvdFilmIta verrà impostata come traccia audio di default la traccia 
    \titaliana. Nei preset che iniziano con dvdFilm verrà disattivata la traccia sottotitoli di default.\n
    \tI preset che iniziano con dvdExtra cercheranno di impostare e mantenere come traccia audio di default 
    \tl'inglese e di settare come traccia sottotitoli di default la lingua specificata dopo dvdExtra.\n
    Nella seguente parte del nome ci sono le informazioni sui codec da usare per la compressione:\n
    \tH264 farà usare il codec h264 con le impostazioni di default di ffmpeg
    \tCopyRest significa che bisogna solo copiare gli stream rimanenti, quindi, H264CopyRest significa che 
    \tbisogna comprimere lo stream video in h264 e lasciare invariati gli stream audio e sottotitoli\n
    \tCopyAll significa che bisogna copiare tutti gli stream (video, audio, sottotitoli) senza comprimerli
    \tL'ultima parte del nome del preset è dedicato al formato del file output, Mkv significa che si vuole 
    \tcreare un file .mkv''')
    print()
    print('-d, --debug')
    print('''
    Attiva la modalità debug stampando più informazioni possibili sullo stdout
    ''')
    print()
    print('-h, --help')
    print('''
    Stampa sullo stdout questa guida ed esce
    ''')
    print()
    print('-v, --version')
    print('''
    Stampa sullo stdout la versione del software ed esce
    ''')
    print()

def setFfprobe():
    ffprobe = '/usr/bin/ffprobe'
    if(not os.path.isfile(ffprobe)):
        raise ValueError("ffprobe non trovato in " + ffprobe)
    probeOptions = ['-hide_banner']
    # probeOptions += ['-print_format', 'json']
    return (ffprobe, probeOptions)

def setFfmpeg(fileMovie):
    ffmpeg = '/usr/bin/ffmpeg'
    if(not os.path.isfile(ffmpeg)):
        raise ValueError("ffmpeg non trovato in " + ffmpeg)
    encodeOptions = ['-hide_banner']
    encodeOptions += ['-i', '\'' + fileMovie + '\'']
    return (ffmpeg, encodeOptions)

def setPreset(preset, defaultPreset):
    if(preset == ''):
        print('Non hai impostato alcun preset, uso ' + defaultPreset)
        return defaultPreset
    else:
        if(preset == 'dvdFilmItaH264CopyRestMkv' or preset == 'dvdFilmItaCopyAllMkv' or 
        preset == 'dvdExtraItaH264CopyRestMkv' or preset == 'dvdExtraItaCopyAllMkv'):
            return preset
        else:
            print('\nPreset inserito non valido.')
            printPresets()
            print()
            sys.exit(2)

def makePreset(preset):
    if(preset == 'dvdFilmItaH264CopyRestMkv'):
        presetSettings = (
            'h264', # videoCodec
            '23', # videoCRF
            'copy', # audioCodec
            'copy', # subsCodec
            'ita', # defaultAudioLang
            True, # disableSubs
            None, # defaultSubsLang
            None, # subsDefault
            None, # newSubsDefault
            'mkv' # outExt
        )
    elif(preset == 'dvdFilmItaCopyAllMkv'):
        presetSettings = (
            'copy', # videoCodec
            None, # videoCRF
            'copy', # audioCodec
            'copy', # subsCodec
            'ita', # defaultAudioLang
            True, # disableSubs
            None, # defaultSubsLang
            None, # subsDefault
            None, # newSubsDefault
            'mkv' # outExt
        )
    elif(preset == 'dvdExtraItaH264CopyRestMkv'):
        presetSettings = (
            'h264', # videoCodec
            '23', # videoCRF
            'copy', # audioCodec
            'copy', # subsCodec
            'eng', # defaultAudioLang
            False, # disableSubs
            'ita', # defaultSubsLang
            0, # subsDefault
            0, # newSubsDefault
            'mkv' # outExt
        )
    elif(preset == 'dvdExtraItaCopyAllMkv'):
        presetSettings = (
            'copy', # videoCodec
            None, # videoCRF
            'copy', # audioCodec
            'copy', # subsCodec
            'eng', # defaultAudioLang
            False, # disableSubs
            'ita', # defaultSubsLang
            0, # subsDefault
            0, # newSubsDefault
            'mkv' # outExt
        )
    else:
        # Lascio questo else per eventuali usi futuri, qua, grazie a setPreset non ci si arriverà mai
        print('Preset non disponibile')
        sys.exit(2)
    return presetSettings

def getPathInputInfos(fileMovie):
    return(os.path.dirname(fileMovie), os.path.basename(fileMovie))

def execProbe(ffprobe, probeOptions, fileMovie):
    probeCommand = [ffprobe] + probeOptions + [fileMovie]
    proc = subprocess.Popen(probeCommand, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    return proc.communicate()

def printProbeInfo(streamsCount, streamsVideo, streamsAudio, streamsSubs):
    print()
    print(str(streamsCount),'Tracce Totali')
    print(str(streamsVideo),'Tracce video')
    print(str(streamsAudio),'Tracce audio')
    print(str(streamsSubs),'Tracce sottotitoli')
    print()

def inputIsAMovie(streamsCount, streamsVideo, streamsAudio, streamsSubs):
    if((streamsCount > 0) and (streamsVideo > 0 or streamsAudio > 0 or streamsSubs > 0)):
        return True
    else:
        return False

def setOutputFile(prefix, fileMovie, outputFile, outExt):
    inputDir, inputFile = getPathInputInfos(fileMovie)
    if(outputFile == ''):
        if(inputDir == ''): 
            return '\'./' + prefix + '.' + inputFile + '.' + outExt + '\''
        else:
            return '\'' + inputDir + '/' + prefix + '.' + inputFile + '.' + outExt + '\''
    else:
        if(inputDir == ''): 
            return '\'' + outputFile + '.' + outExt + '\''
        else:
            if(os.path.dirname(outputFile) == ''):
                return '\'' + inputDir + '/' + outputFile + '.' + outExt + '\''
            else:
                return '\'' + outputFile + '.' + outExt + '\''

def commandLineOutput(preset, encodeCommand):
    print()
    print('Lancia il seguente comando per rippare con il preset selezionato ('+preset+'):')
    print()
    print(' '.join(encodeCommand))
    print()

try:
    opts, args = getopt.getopt(sys.argv[1:],"dvhsi:p:o:",["debug","version","help","stripmeta","input=","preset=","output="])
except getopt.GetoptError:
    printHelp()
    sys.exit(2)
print()
for opt, arg in opts:
    if opt in ("-h", "--help"):
        printHelp()
        sys.exit()
    elif opt in ("-i", "--input"):
        if(checkInputFile(arg)):
            fileMovie = arg
    elif opt in ("-p", "--preset"):
        preset = arg
    elif opt in ("-o", "--output"):
        outputFile = arg
    elif opt in ("-s", "--stripmeta"):
        print('Attenzione: Si è scelto di togliere TUTTI i metadata non ufficiali ffmpeg')
        stripMeta = True
    elif opt in ("-d", "--debug"):
        print('Modalità debug attiva\n')
        verboseMode = True
    elif opt in ("-v", "--version"):
        print(swName + ' v' + swVersion)
        sys.exit()

if(fileMovie == ''):
    print('Devi specificare almeno il file di input\n')
    printHelp()
    sys.exit(2)

ffprobe, probeOptions = setFfprobe()
ffmpeg, encodeOptions = setFfmpeg(fileMovie)

preset = setPreset(preset, defaultPreset)
videoCodec, videoCRF, audioCodec, subsCodec, defaultAudioLang, disableSubs, defaultSubsLang, subsDefault, newSubsDefault, outExt = makePreset(preset)

out, err = execProbe(ffprobe, probeOptions, fileMovie)
# print(out) # DEBUG
# print(err) # DEBUG # ffprobe print to stderr

buf = io.BytesIO(err)
line = buf.readline()

streamsCount = 0
streamsVideo = 0
streamsAudio = 0
streamsSubs = 0

mapPart = []
videoEncPart = []
audioEncPart = []
audioMetaPart = []
subsEncPart = []
subsMetaPart = []

audioDefault = 0
newAudioDefault = 0 # Dummy, sarà settato in seguito
subsDefault = 0
newSubsDefault = 0 # Dummy, sarà settato in seguito

while line:
    if(verboseMode):
        pass
        # print(line.strip()) # DEBUG
    if(line.strip().startswith(b'Stream')):
        if(verboseMode):
            print('STREAM 0:' + str(streamsCount))
            print(line.strip().split(b': ')) # DEBUG
        if(line.strip().split(b': ')[1] == b'Video'):
            if(verboseMode):
                print('Traccia video trovata !!!\n')
            if(videoCodec == 'copy'):
                videoEncPart = ['-c:v:'+str(streamsVideo), 'copy']
            else:
                videoEncPart = ['-vcodec', videoCodec, 
                                '-crf', videoCRF]
            streamsVideo+=1
        if(line.strip().split(b': ')[1] == b'Audio'):
            if(verboseMode):
                print('Traccia audio trovata !!!\n')
            if(audioCodec == 'copy'):
                audioEncPart += ['-c:a:'+str(streamsAudio), 'copy']
            if(line.strip().split(b': ')[2].endswith(b'(default)')):
                audioDefault = streamsAudio
            if(line.strip().split(b': ')[0].endswith(b'('+str.encode(defaultAudioLang)+b')')):
                newAudioDefault = streamsAudio
            if(verboseMode):
                print('Lingua traccia 0:'+str(streamsCount)+' => ' + line.strip().split(b': ')[0].split(b'(')[1].split(b')')[0].decode('utf-8')) # DEBUG
            audioMetaPart += ['-metadata:s:a:'+str(streamsAudio)+' language='+(line.strip().split(b': ')[0].split(b'(')[1].split(b')')[0]).decode('utf-8')]
            streamsAudio+=1
        if(line.strip().split(b': ')[1] == b'Subtitle'):
            if(verboseMode):
                print('Traccia sottotitolo trovata !!!\n')
            if(subsCodec == 'copy'):
                subsEncPart += ['-c:s:'+str(streamsSubs), 'copy']
            if(line.strip().split(b': ')[2].endswith(b'(default)')):
                subsDefault = streamsSubs
            if(defaultSubsLang != None):
                if(line.strip().split(b': ')[0].endswith(b'('+str.encode(defaultSubsLang)+b')')):
                    newSubsDefault = streamsSubs
            if(verboseMode):
                print('Lingua traccia 0:'+str(streamsCount)+' => ' + line.strip().split(b': ')[0].split(b'(')[1].split(b')')[0]) # DEBUG
            subsMetaPart += ['-metadata:s:s:'+str(streamsSubs)+' language='+(line.strip().split(b': ')[0].split(b'(')[1].split(b')')[0]).decode('utf-8')]
            streamsSubs+=1
        mapPart += ['-map', '0:'+str(streamsCount)]
        streamsCount+=1
    line = buf.readline()

printProbeInfo(streamsCount, streamsVideo, streamsAudio, streamsSubs)
if(not inputIsAMovie(streamsCount, streamsVideo, streamsAudio, streamsSubs)):
    print('Il file di input di input non sembra essere un file video\n')
    sys.exit(2)

encodeOptions += mapPart + videoEncPart + audioEncPart + subsEncPart
if(streamsAudio > 0):
    encodeOptions += ['-disposition:a:'+str(audioDefault), 'none']
    encodeOptions += ['-disposition:a:'+str(newAudioDefault), 'default']
if(streamsSubs > 0):
    if(disableSubs):
        encodeOptions += ['-disposition:s:'+str(subsDefault), 'none']
    else:
        encodeOptions += ['-disposition:s:'+str(subsDefault), 'none']
        encodeOptions += ['-disposition:s:'+str(newSubsDefault), 'default']

if(stripMeta):
    encodeOptions += ['-map_metadata -1']

encodeOptions += audioMetaPart
encodeOptions += subsMetaPart
# encodeOptions += ['-metadata:s:s:0 language=ita'] # PseudoCode

encodeCommand = [ffmpeg] + encodeOptions + [setOutputFile(prefix, fileMovie, outputFile, outExt)]

if(verboseMode):
    print('ffmpeg mapping options: ') # DEBUG
    print(mapPart) # DEBUG
    print() # DEBUG
    print('ffmpeg video encoding options: ') # DEBUG
    print(videoEncPart) # DEBUG
    print() # DEBUG
    print('ffmpeg audio encoding options: ') # DEBUG
    print(audioEncPart) # DEBUG
    print() # DEBUG
    print('ffmpeg subtitles encoding options: ') # DEBUG
    print(subsEncPart) # DEBUG
    print() # DEBUG
    print('ffmpeg merged encode options: ') # DEBUG
    print(encodeOptions) # DEBUG
    print() # DEBUG
    print('ffmpeg complete: ') # DEBUG
    print(encodeCommand) # DEBUG

commandLineOutput(preset, encodeCommand)

