'''
ffInterface v1.3
  __  __ ___       _             __ 
 / _|/ _|_ _|_ __ | |_ ___ _ __ / _| __ _  ___ ___ 
| |_| |_ | || '_ \| __/ ._\ '__| |_ / _` |/  _/ ._\
|_| |_| |___|_| |_|\__\___|_|  |_|  \__,_|\___\___|

Rielabora le info di ffprobe per generare comandi ffmpeg secondo presets
Si poteva usare solo Bash? Si

1) Ora viene considerato solo lo stream 0 ed i suoi substreams 
che sono per proprietà traansitiva intesi come streams, per il futuro
fare in modo che vengano trattati tutti gli stream padre se esistenti 
e non solo lo 0, di conseguenza, ogni stream padre avrà N substreams
2) Mettere un'interfaccia (che sia GTK, QT o qualsiasi altra cosa)
3) Ci sono problemi se il file non ha tracce sottotoli o se non ci sono 
sub di default.. (PROBABILMENTE RISOLTO)

Testato con ffprobe e ffmpeg 3.4.4

Questo codice è brutale e probabilmente non è pythonista.
Don't try this at home.
'''

import subprocess
import io
import os
import sys, getopt

###############################################################################
# Inizio dichiarazione classe FfInterface #####################################
###############################################################################

class FfInterface:

    def __init__(self):
        self.swName = os.path.basename(__file__, prefix = 'n4d46t3m')
        self.swVersion = '1.3'
        self.fileMovie = ''
        self.outputFile = ''
        self.defaultPreset = 'dvdFilmItaH264CopyRestMkv'
        self.preset = ''
        self.presetSettings = ()
        self.prefix = prefix
        self.stripMeta = False
        self.verboseMode = False
        self.streamsCount = 0
        self.streamsVideo = 0
        self.streamsAudio = 0
        self.streamsSubs = 0
        self.mapPart = []
        self.videoEncPart = []
        self.audioEncPart = []
        self.audioMetaPart = []
        self.subsEncPart = []
        self.subsMetaPart = []
        self.encodeOptions = []
    
    def checkInputFile(self):
        if(not os.path.isfile(self.fileMovie)):
            raise ValueError("File di input non trovato")
        else:
            return True

    def printPresets(self):
        print('''
        Preset disponibili:
        \tdvdFilmItaH264CopyRestMkv
        \tdvdFilmItaCopyAllMkv
        \tdvdExtraItaH264CopyRestMkv
        \tdvdExtraItaCopyAllMkv''')

    def printHelp(self):
        print()
        print(self.swName + ' v' + self.swVersion, end='')
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
        self.printPresets()
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

    def manageOptions(self):
        try:
            opts, args = getopt.getopt(sys.argv[1:],"dvhsi:p:o:",["debug","version","help","stripmeta","input=","preset=","output="])
        except getopt.GetoptError:
            self.printHelp()
            sys.exit(2)
        print()
        for opt, arg in opts:
            if opt in ("-h", "--help"):
                self.printHelp()
                sys.exit()
            elif opt in ("-i", "--input"):
                self.fileMovie = arg
                if(self.checkInputFile()):
                    pass
            elif opt in ("-p", "--preset"):
                self.preset = arg
            elif opt in ("-o", "--output"):
                self.outputFile = arg
            elif opt in ("-s", "--stripmeta"):
                print('Attenzione: Si è scelto di togliere TUTTI i metadata non ufficiali ffmpeg')
                self.stripMeta = True
            elif opt in ("-d", "--debug"):
                print('Modalità debug attiva\n')
                self.verboseMode = True
            elif opt in ("-v", "--version"):
                print(self.swName + ' v' + self.swVersion)
                sys.exit()

    def setFfprobe(self):
        ffprobe = '/usr/bin/ffprobe'
        if(not os.path.isfile(ffprobe)):
            raise ValueError("ffprobe non trovato in " + ffprobe)
        probeOptions = ['-hide_banner']
        # probeOptions += ['-print_format', 'json']
        return (ffprobe, probeOptions)

    def setFfmpeg(self):
        ffmpeg = '/usr/bin/ffmpeg'
        if(not os.path.isfile(ffmpeg)):
            raise ValueError("ffmpeg non trovato in " + ffmpeg)
        self.encodeOptions = ['-hide_banner']
        self.encodeOptions += ['-i', '\'' + self.fileMovie + '\'']
        return (ffmpeg, self.encodeOptions)

    def setPreset(self):
        if(self.preset == ''):
            print('Non hai impostato alcun preset, uso ' + self.defaultPreset)
            self.preset = self.defaultPreset
        else:
            if(self.preset == 'dvdFilmItaH264CopyRestMkv' or self.preset == 'dvdFilmItaCopyAllMkv' or 
            self.preset == 'dvdExtraItaH264CopyRestMkv' or self.preset == 'dvdExtraItaCopyAllMkv'):
                pass
            else:
                print('\nPreset inserito non valido.')
                self.printPresets()
                print()
                sys.exit(2)

    def makePreset(self):
        if(self.preset == 'dvdFilmItaH264CopyRestMkv'):
            self.presetSettings = (
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
        elif(self.preset == 'dvdFilmItaCopyAllMkv'):
            self.presetSettings = (
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
        elif(self.preset == 'dvdExtraItaH264CopyRestMkv'):
            self.presetSettings = (
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
        elif(self.preset == 'dvdExtraItaCopyAllMkv'):
            self.presetSettings = (
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
        return self.presetSettings

    def getPathInputInfos(self):
        return(os.path.dirname(self.fileMovie), os.path.basename(self.fileMovie))

    def execProbe(self, ffprobe, probeOptions):
        probeCommand = [ffprobe] + probeOptions + [self.fileMovie]
        proc = subprocess.Popen(probeCommand, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        return proc.communicate()

    def printProbeInfo(self):
        print()
        print(str(self.streamsCount),'Tracce Totali')
        print(str(self.streamsVideo),'Tracce video')
        print(str(self.streamsAudio),'Tracce audio')
        print(str(self.streamsSubs),'Tracce sottotitoli')
        print()

    def inputIsAMovie(self):
        if((self.streamsCount > 0) and (self.streamsVideo > 0 or self.streamsAudio > 0 or self.streamsSubs > 0)):
            return True
        else:
            return False

    def setOutputFile(self, outExt):
        inputDir, inputFile = self.getPathInputInfos()
        if(self.outputFile == ''):
            if(inputDir == ''): 
                return '\'./' + self.prefix + '.' + inputFile + '.' + outExt + '\''
            else:
                return '\'' + inputDir + '/' + self.prefix + '.' + inputFile + '.' + outExt + '\''
        else:
            if(inputDir == ''): 
                return '\'' + self.outputFile + '.' + outExt + '\''
            else:
                if(os.path.dirname(self.outputFile) == ''):
                    return '\'' + inputDir + '/' + self.outputFile + '.' + outExt + '\''
                else:
                    return '\'' + self.outputFile + '.' + outExt + '\''

    def composeCommand(self, out, err):
        buf = io.BytesIO(err)
        line = buf.readline()

        audioDefault = 0
        newAudioDefault = 0 # Dummy, sarà settato in seguito
        subsDefault = 0
        newSubsDefault = 0 # Dummy, sarà settato in seguito

        while line:
            if(self.verboseMode):
                pass
                # print(line.strip()) # DEBUG
            if(line.strip().startswith(b'Stream')):
                if(self.verboseMode):
                    print('STREAM 0:' + str(self.streamsCount))
                    print(line.strip().split(b': ')) # DEBUG
                if(line.strip().split(b': ')[1] == b'Video'):
                    if(self.verboseMode):
                        print('Traccia video trovata !!!\n')
                    if(videoCodec == 'copy'):
                        self.videoEncPart = ['-c:v:'+str(self.streamsVideo), 'copy']
                    else:
                        self.videoEncPart = ['-vcodec', videoCodec, 
                                        '-crf', videoCRF]
                    self.streamsVideo+=1
                if(line.strip().split(b': ')[1] == b'Audio'):
                    if(self.verboseMode):
                        print('Traccia audio trovata !!!\n')
                    if(audioCodec == 'copy'):
                        self.audioEncPart += ['-c:a:'+str(self.streamsAudio), 'copy']
                    if(line.strip().split(b': ')[2].endswith(b'(default)')):
                        audioDefault = self.streamsAudio
                    if(line.strip().split(b': ')[0].endswith(b'('+str.encode(defaultAudioLang)+b')')):
                        newAudioDefault = self.streamsAudio
                    if(self.verboseMode):
                        print('Lingua traccia 0:'+str(self.streamsCount)+' => ' + line.strip().split(b': ')[0].split(b'(')[1].split(b')')[0].decode('utf-8')) # DEBUG
                    self.audioMetaPart += ['-metadata:s:a:'+str(self.streamsAudio)+' language='+(line.strip().split(b': ')[0].split(b'(')[1].split(b')')[0]).decode('utf-8')]
                    self.streamsAudio+=1
                if(line.strip().split(b': ')[1] == b'Subtitle'):
                    if(self.verboseMode):
                        print('Traccia sottotitolo trovata !!!\n')
                    if(subsCodec == 'copy'):
                        self.subsEncPart += ['-c:s:'+str(self.streamsSubs), 'copy']
                    if(line.strip().split(b': ')[2].endswith(b'(default)')):
                        subsDefault = self.streamsSubs
                    if(defaultSubsLang != None):
                        if(line.strip().split(b': ')[0].endswith(b'('+str.encode(defaultSubsLang)+b')')):
                            newSubsDefault = self.streamsSubs
                    if(self.verboseMode):
                        print('Lingua traccia 0:'+str(self.streamsCount)+' => ' + line.strip().split(b': ')[0].split(b'(')[1].split(b')')[0]) # DEBUG
                    self.subsMetaPart += ['-metadata:s:s:'+str(self.streamsSubs)+' language='+(line.strip().split(b': ')[0].split(b'(')[1].split(b')')[0]).decode('utf-8')]
                    self.streamsSubs+=1
                self.mapPart += ['-map', '0:'+str(self.streamsCount)]
                self.streamsCount+=1
            line = buf.readline()
        self.encodeOptions += self.mapPart + self.videoEncPart + self.audioEncPart + self.subsEncPart
        if(self.streamsAudio > 0):
            self.encodeOptions += ['-disposition:a:'+str(audioDefault), 'none']
            self.encodeOptions += ['-disposition:a:'+str(newAudioDefault), 'default']
        if(self.streamsSubs > 0):
            if(disableSubs):
                self.encodeOptions += ['-disposition:s:'+str(subsDefault), 'none']
            else:
                self.encodeOptions += ['-disposition:s:'+str(subsDefault), 'none']
                self.encodeOptions += ['-disposition:s:'+str(newSubsDefault), 'default']
        if(self.stripMeta):
            self.encodeOptions += ['-map_metadata -1']
        self.encodeOptions += self.audioMetaPart
        self.encodeOptions += self.subsMetaPart
        return self.encodeOptions

    def printCommandInfos(self):
        if(self.verboseMode):
            print('ffmpeg mapping options: ') # DEBUG
            print(self.mapPart) # DEBUG
            print() # DEBUG
            print('ffmpeg video encoding options: ') # DEBUG
            print(self.videoEncPart) # DEBUG
            print() # DEBUG
            print('ffmpeg audio encoding options: ') # DEBUG
            print(self.audioEncPart) # DEBUG
            print() # DEBUG
            print('ffmpeg subtitles encoding options: ') # DEBUG
            print(self.subsEncPart) # DEBUG
            print() # DEBUG
            print('ffmpeg merged encode options: ') # DEBUG
            print(self.encodeOptions) # DEBUG
            print() # DEBUG
            print('ffmpeg complete: ') # DEBUG
            print(encodeCommand) # DEBUG

    def commandLineOutput(self, encodeCommand):
        print()
        print('Lancia il seguente comando per rippare con il preset selezionato ('+self.preset+'):')
        print()
        print(' '.join(encodeCommand))
        print()

###############################################################################
# Fine dichiarazione classe FfInterface #######################################
###############################################################################

if __name__ == "__main__":
    
    ffWrapper = FfInterface()
    ffWrapper.manageOptions()
    ffprobe, probeOptions = ffWrapper.setFfprobe()
    ffmpeg, encodeOptions = ffWrapper.setFfmpeg()
    ffWrapper.setPreset()
    videoCodec, videoCRF, audioCodec, subsCodec, defaultAudioLang, disableSubs, defaultSubsLang, subsDefault, newSubsDefault, outExt = ffWrapper.makePreset()
    out, err = ffWrapper.execProbe(ffprobe, probeOptions)
    # print(out) # DEBUG
    # print(err) # DEBUG # ffprobe print to stderr
    encodeOptions = ffWrapper.composeCommand(out, err)
    ffWrapper.printProbeInfo()
    if(not ffWrapper.inputIsAMovie()):
        print('Il file di input di input non sembra essere un file video\n')
        sys.exit(2)

    encodeCommand = [ffmpeg] + encodeOptions + [ffWrapper.setOutputFile(outExt)]
    ffWrapper.printCommandInfos()
    ffWrapper.commandLineOutput(encodeCommand)

