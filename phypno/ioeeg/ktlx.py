"""Module reads and writes header and data for KTLX data. The files are:
  - .eeg (patient information)
  - .ent (notes, sometimes with a backup file called .ent.old)
  - .erd (raw data)
  - .etc (table of content)
  - .snc (synchronization file)
  - .stc (segmented table of content)
  - .vtc (video table of content)
  - .avi (videos)

There is only one of these files in the directory, except for .erd, .etc., .avi
These files are numbered in the format _%03d, except for the first one, which
is not _000 but there is no extension, for backwards compatibility.

This module contains functions to read each of the files, the files are called
_read_EXT where EXT is one of the extensions.

TODO: check all the times, if they are 1. internally consistent and 2.
meaningful. Absolute time is stored in the header of all the files, and in
.snc. In addition, check the 'start_stamp' in .erd does not start at zero.

"""
from __future__ import division
from binascii import hexlify
from datetime import timedelta, datetime
from glob import glob
from logging import info
from math import ceil
from numpy import zeros, ones, concatenate, expand_dims, where, cumsum, array
from os import SEEK_END
from os.path import basename, join, exists, splitext
from re import sub
from struct import unpack


BITS_IN_BYTE = 8
# http://support.microsoft.com/kb/167296
# How To Convert a UNIX time_t to a Win32 FILETIME or SYSTEMTIME
EPOCH_AS_FILETIME = 116444736000000000  # January 1, 1970 as MS file time
HUNDREDS_OF_NANOSECONDS = 10000000

ZERO = timedelta(0)
HOUR = timedelta(hours=1)


def _calculate_conversion(hdr):
    """Calculate the conversion factor.

    Returns
    -------
    conv_factor : numpy.ndarray
        channel-long vector with the channel-specific conversion factor

    Notes
    -----
    Ktlx system converts into microvolts, but here we convert to volts, which
    are more readible for our recordings.

    """
    discardbits = hdr['discardbits']
    n_chan = hdr['num_channels']

    if hdr['headbox_type'][0] in (1, 3):
        # all channels
        factor = ones((n_chan)) * (8711. / (221 - 0.5)) * 2 ** discardbits

    elif hdr['headbox_type'][0] == 4:
        # 0 - 23
        ch1 = ones((24)) * (8711. / (221 - 0.5)) * 2 ** discardbits
        # 24 - 27
        ch2 = ones((4)) * ((5000000. / (210 - 0.5)) / 26) * 2 ** discardbits

        factor = concatenate((ch1, ch2))

    elif hdr['headbox_type'][0] == 21:
        # 0 -127
        ch1 = ones((128)) * (8711. / (221 - 0.5)) * 2 ** discardbits
        # 128 - 129
        ch2 = ones((2)) * (1 / 26) * 2 ** discardbits
        # 130 - 255
        ch3 = ones((126)) * (8711. / (221 - 0.5)) * 2 ** discardbits

        factor = concatenate((ch1, ch2, ch3))

    elif hdr['headbox_type'][0] == 22:
        # 0 -31
        ch1 = ones((32)) * (8711. / (221 - 0.5)) * 2 ** discardbits
        # 32 - 39
        ch2 = ones((8)) * ((10800000. / 65536.) / 26) * 2 ** discardbits
        # 40 - 41
        ch3 = ones((2)) * (1 / 26) * 2 ** discardbits
        # 42
        ch4 = ones((1)) * ((10800000. / 65536.) / 26) * 2 ** discardbits

        factor = concatenate((ch1, ch2, ch3, ch4))

    else:
        raise NotImplementedError('Implement conversion factor for headbox ' +
                                  str(hdr['headbox_type'][0]))

    return factor[:n_chan] * 1e-6


def _filetime_to_dt(ft):
    """Converts a Microsoft filetime number to a Python datetime. The new
    datetime object is time zone-naive but is equivalent to tzinfo=utc.

    """
    # Get seconds and remainder in terms of Unix epoch
    s, ns100 = divmod(ft - EPOCH_AS_FILETIME, HUNDREDS_OF_NANOSECONDS)
    # Convert to datetime object
    dt = datetime.utcfromtimestamp(s)
    # Add remainder in as microseconds. Python 3.2 requires an integer
    dt = dt.replace(microsecond=(ns100 // 10))
    return dt


def _make_str(t_in):
    t_out = []
    for t in t_in:
        if t == b'\x00':
            break
        t_out.append(t.decode('utf-8'))
    return ''.join(t_out)


def _read_eeg(eeg_file):
    """Reads eeg file, but it doesn't work, the data is in text format, but
    based on Excel. You can read it from the editor, there are still a couple
    of signs that are not in Unicode.

    TODO: parse the text of EEG, if it's interesting

    Notes
    -----
    The patient information file consists of a single null terminated string
    following the generic file header. The string encodes all the patient
    information in a list format defined by a hierarchy of name value pairs.

    """
    pass


def _read_ent(ent_file):
    """Read notes stored in .ent file.

    This is a basic implementation, that relies on turning the information in
    the string in the dict format, and then evaluate it. It's not very flexible
    and it might not read some notes, but it's fast. I could not implement a
    nice, recursive approach.

    Notes
    -----
    TODO:
        in Python 3, it doesn't read the note, I think it needs to be converted
        somewhere, but I don't know where.

    """
    with open(ent_file, 'rb') as f:
        f.seek(352)  # end of header

        note_hdr_length = 16

        allnote = []
        while True:
            note = {}
            note['type'], = unpack('i', f.read(4))
            note['length'], = unpack('i', f.read(4))
            note['prev_length'], = unpack('i', f.read(4))
            note['unused'], = unpack('i', f.read(4))
            if not note['type']:
                break
            s = f.read(note['length'] - note_hdr_length)
            s = s[:-2]  # it ends with one empty byte
            try:
                s1 = s.replace('\n', ' ')
                s1 = s1.replace('\\xd ', '')
                s1 = s1.replace('(.', '{')
                s1 = s1.replace(')', '}')
                s1 = s1.replace('",', '" :')
                s1 = s1.replace('{"', '"')
                s1 = s1.replace('},', ',')
                s1 = s1.replace('}}', '}')
                s1 = sub(r'\(([0-9 ,-\.]*)\}', r'[\1]', s1)
                note['value'] = eval(s1)
                allnote.append(note)
            except:
                pass
    return allnote


def _read_erd(erd_file, n_samples):
    """Read the raw data and return a matrix, converted to microvolts.

    Parameters
    ----------
    erd_file : str
        one of the .erd files to read
    n_samples : int
        the number of samples to read, based on .stc

    Returns
    -------
    data : numpy.ndarray
        2d matrix with the data, as read from the file

    Error
    -----
    It checks whether the event byte (the first byte) is x00 as expected.
    It can also be x01, meaning that an event was generated by an external
    trigger. According to the manual, "a photic stimulator is the only
    supported device which generates an external trigger."
    If the eventbyte is something else, it throws an error.

    Notes
    -----
    Each sample point consists of these parts:
      - Event Byte
      - Frequency byte (only if file_schema >= 8 and one chan has != freq)
      - Delta mask (only if file_schema >= 8)
      - Delta Information
      - Absolute Channel Values

    Event Byte:
      Bit 0 of the event byte indicates the presence of the external trigger
      during the sample period. It's very rare.

    Delta Mask:
      Bit-mask of a size int( number_of_channels / 8 + 0.5). Each 1 in the mask
      indicates that corresponding channel has 2*n bit delta, 0 means that
      corresponding channel has n bit delta.
      The rest of the byte of the delta mask is filled with "1".
      If file_schema <= 7, it generates a "fake" delta, where everything is 0.

    """
    hdr = _read_hdr_file(erd_file)
    n_chan = hdr['num_channels']
    l_deltamask = int(ceil(n_chan / BITS_IN_BYTE))  # deltamask length

    with open(erd_file, 'rb') as f:
        filebytes = f.read()

    if hdr['file_schema'] in (7,):
        i = 4560
        abs_delta = b'\x80'  # one byte: 10000000

    if hdr['file_schema'] in (8, 9):
        i = 8656
        abs_delta = b'\xff\xff'

    output = zeros((n_chan, n_samples))

    for sam in range(n_samples):

        # Event Byte
        eventbite = filebytes[i:i+1]
        i += 1
        if eventbite == b'':
            break
        try:
            assert eventbite in (b'\x00', b'\x01')
            info('eventbite: ' + str(eventbite))
        except:
            Exception('at pos ' + str(i) +
                      ', eventbite (should be x00 or x01): ' + str(eventbite))

        # Delta Information
        if hdr['file_schema'] in (7,):
            deltamask = '0' * n_chan

        if hdr['file_schema'] in (8, 9):
            # read single bits as they appear, one by one
            byte_deltamask = unpack('B' * l_deltamask,
                                    filebytes[i:i+l_deltamask])
            i += l_deltamask
            deltamask = ['{0:08b}'.format(x)[::-1] for x in byte_deltamask]
            deltamask = ''.join(deltamask)
            info('deltamask: ' + deltamask)

        absvalue = [False] * n_chan
        info_toread = ''
        for i_c, m in enumerate(deltamask[:n_chan]):
            if m == '1':
                val = filebytes[i:i+2]
                i += 2
            elif m == '0':
                val = filebytes[i:i+1]
                i += 1

            if val == abs_delta:
                absvalue[i_c] = True  # read the full value below
                info_toread += 'T'
            else:
                if m == '1':
                    output[i_c, sam] = output[i_c, sam - 1] + unpack('h',
                                                                     val)[0]
                elif m == '0':
                    output[i_c, sam] = output[i_c, sam - 1] + unpack('b',
                                                                     val)[0]
                info_toread += 'F'
        info(info_toread)

        for i_c, to_read in enumerate(absvalue):
            if to_read:
                output[i_c, sam] = unpack('i', filebytes[i:i+4])[0]
                i += 4

    factor = _calculate_conversion(hdr)
    return expand_dims(factor, 1) * output


def _read_etc(etc_file):
    """Return information about etc.

    ETC contains only 4 4-bytes, I cannot make sense of it. The EEG file format
    does not have an explanation for ETC, it says it's similar to the end of
    STC, which has 4 int, but the values don't match.

    """
    with open(etc_file, 'rb') as f:
        f.seek(352)  # end of header
        v1 = unpack('i', f.read(4))[0]
        v2 = unpack('i', f.read(4))[0]
        v3 = unpack('i', f.read(4))[0]  # always zero?
        v4_a = unpack('h', f.read(2))[0]  # they look like two values
        v4_b = unpack('h', f.read(2))[0]  # maybe this one is unsigned (H)

        f.seek(352)  # end of header
        info(hexlify(f.read(16)))
    return v1, v2, v3, (v4_a, v4_b)


def _read_snc(snc_file):
    """Read Synchronization File and return sample stamp and time

    Returns
    -------
    sampleStamp : list of int
        Sample number from start of study
    sampleTime : list of datetime.datetime
        File time representation of sampleStamp

    Notes
    -----
    TODO: check if the timing is accurate

    The synchronization file is used to calculate a FILETIME given a sample
    stamp (and vise-versa). Theoretically, it is possible to calculate a sample
    stamp's FILETIME given the FILETIME of sample stamp zero (when sampling
    started) and the sample rate. However, because the sample rate cannot be
    represented with full precision the accuracy of the FILETIME calculation is
    affected.

    To compensate for the lack of accuracy, the synchronization file maintains
    a sample stamp-to-computer time (called, MasterTime) mapping. Interpolation
    is then used to calculate a FILETIME given a sample stamp (and vise-versa).

    The attributes, sampleStamp and sampleTime, are used to predict (using
    interpolation) the FILETIME based upon a given sample stamp (and
    vise-versa). Currently, the only use for this conversion process is to
    enable correlation of EEG (sample_stamp) data with other sources of data
    such as Video (which works in FILETIME).

    """
    with open(snc_file, 'r') as f:
        f.seek(0, SEEK_END)
        endfile = f.tell()
        f.seek(352)  # end of header

        sampleStamp = []
        sampleTime = []
        while True:
            sampleStamp.append(unpack('i', f.read(4))[0])
            sampleTime.append(_filetime_to_dt(unpack('l', f.read(8))[0]))
            if f.tell() == endfile:
                break
        return sampleStamp, sampleTime


def _read_stc(stc_file):
    """Read Segment Table of Contents file.

    Returns
    -------
    hdr : dict
        - next_segment : Sample frequency in Hertz
        - final : Number of channels stored
        - padding : Padding

    all_stamp : list of dict
        - segment_name : Name of ERD / ETC file segment
        - start_stamp : First sample stamp that is found in the ERD / ETC pair
        - end_stamp : Last sample stamp that is still found in the ERD / ETC
        pair
        - sample_num : Number of samples recorded to the point that corresponds
        to start_stamp. This number accumulates over ERD / ETC pairs and is
        equal to sample_num of the first entry in the ETC file referenced by
        this STC entry


    Notes
    -----
    The Segment Table of Contents file is an index into pairs of (raw data file
    / table of contents file). It is used for mapping samples file segments.
    EEG raw data is split into segments in order to break a single file size
    limit (used to be 2GB) while still allowing quick searches. This file ends
    in the extension '.stc'. Default segment size (size of ERD file after which
    it is closed and new [ERD / ETC] pair is opened) is 50MB. The file starts
    with a generic EEG file header, and is followed by a series of fixed length
    records called the STC entries. ERD segments are named according to the
    following schema:
      - <FIRST_NAME>, <LAST_NAME>_<GUID>.ERD (first)
      - <FIRST_NAME>, <LAST_NAME>_<GUID>.ETC (first)
      - <FIRST_NAME>, <LAST_NAME>_<GUID>_<INDEX>.ERD (second and subsequent)
      - <FIRST_NAME>, <LAST_NAME>_<GUID>_<INDEX>.ETC (second and subsequent)

    <INDEX> is formatted with "%03d" format specifier and starts at 1 (initial
    value being 0 and omitted for compatibility with the previous versions).

    """
    with open(stc_file, 'rb') as f:
        f.seek(0, SEEK_END)
        endfile = f.tell()
        f.seek(352)  # end of header
        hdr = {}
        hdr['next_segment'] = unpack('i', f.read(4))[0]
        hdr['final'] = unpack('i', f.read(4))[0]
        hdr['padding'] = unpack('i' * 12, f.read(48))

        all_stamp = []

        while True:
            if f.tell() == endfile:
                break
            stamp = {}
            stamp['segment_name'] = _make_str(unpack('c' * 256, f.read(256)))
            stamp['start_stamp'] = unpack('i', f.read(4))[0]
            stamp['end_stamp'] = unpack('i', f.read(4))[0]
            stamp['sample_num'] = unpack('i', f.read(4))[0]
            stamp['sample_span'] = unpack('i', f.read(4))[0]

            all_stamp.append(stamp)

    return hdr, all_stamp


def _read_hdr_file(ktlx_file):
    """Reads header of one KTLX file.

    Parameters
    ----------
    ktlx_file : str
        name of one of the ktlx files inside the directory (absolute path)

    Returns
    -------
    dict
        dict with information about the file

    Notes
    -----
    p.3: says long, but python-long requires 8 bytes, so we use f.read(4)

    GUID is correct, BUT little/big endian problems somewhere

    """
    with open(ktlx_file, 'rb') as f:

        hdr = {}
        assert f.tell() == 0

        hdr['file_guid'] = hexlify(f.read(16))
        hdr['file_schema'], = unpack('H', f.read(2))
        try:
            assert hdr['file_schema'] in (1, 7, 8, 9)
        except:
            raise NotImplementedError('Reading header not implemented for ' +
                                      'file_schema ' + str(hdr['file_schema']))

        hdr['base_schema'], = unpack('H', f.read(2))
        try:  # p.3: base_schema 0 is rare, I think
            assert hdr['base_schema'] == 1
        except:
            raise NotImplementedError('Reading header not implemented for ' +
                                      'base_schema ' + str(hdr['base_schema']))

        hdr['creation_time'] = datetime.fromtimestamp(unpack('i',
                                                             f.read(4))[0])
        hdr['patient_id'], = unpack('i', f.read(4))
        hdr['study_id'], = unpack('i', f.read(4))
        hdr['pat_last_name'] = _make_str(unpack('c' * 80, f.read(80)))
        hdr['pat_first_name'] = _make_str(unpack('c' * 80, f.read(80)))
        hdr['pat_middle_name'] = _make_str(unpack('c' * 80, f.read(80)))
        hdr['patient_id'] = _make_str(unpack('c' * 80, f.read(80)))
        assert f.tell() == 352

        if hdr['file_schema'] >= 7:
            hdr['sample_freq'], = unpack('d', f.read(8))
            hdr['num_channels'], = unpack('i', f.read(4))
            hdr['deltabits'], = unpack('i', f.read(4))
            hdr['phys_chan'] = unpack('i' * hdr['num_channels'],
                                      f.read(hdr['num_channels'] * 4))

            f.seek(4464)
            hdr['headbox_type'] = unpack('i' * 4, f.read(16))
            hdr['headbox_sn'] = unpack('i' * 4, f.read(16))
            hdr['headbox_sw_version'] = _make_str(unpack('c' * 40, f.read(40)))
            hdr['dsp_hw_version'] = _make_str(unpack('c' * 10, f.read(10)))
            hdr['dsp_sw_version'] = _make_str(unpack('c' * 10, f.read(10)))
            hdr['discardbits'], = unpack('i', f.read(4))

        if hdr['file_schema'] >= 8:
            hdr['shorted'] = unpack('h' * 1024, f.read(2048))
            hdr['frequency_factor'] = unpack('h' * 1024, f.read(2048))

    return hdr


class Ktlx():
    def __init__(self, ktlx_dir):
        if isinstance(ktlx_dir, str):
            self.filename = ktlx_dir
            self._hdr = self._read_hdr_dir()

    def _read_hdr_dir(self):
        """Read the header for basic information.

        Returns
        -------
        hdr : dict
          - 'erd': header of .erd file
          - 'stc': general part of .stc file
          - 'stamps' : time stamp for each file

        Also, it adds the attribute
        _basename : str
            the name of the files inside the directory

        """
        eeg_file = join(self.filename, basename(self.filename) + '.eeg')
        if exists(eeg_file):
            self._basename = splitext(basename(self.filename))[0]
        else:  # if the folder was renamed
            eeg_file = glob(join(self.filename, '*.eeg'))
            if len(eeg_file) == 1:
                self._basename = splitext(basename(eeg_file[0]))[0]
            elif len(eeg_file) == 0:
                raise IOError('Could not find any .eeg file.')
            else:
                raise IOError('Found too many .eeg files: ' +
                              '\n'.join(eeg_file))

        hdr = {}

        # use .erd because it has extra info, such as sampling freq
        hdr['erd'] = _read_hdr_file(join(self.filename, self._basename +
                                         '.erd'))

        stc = _read_stc(join(self.filename, self._basename + '.stc'))
        hdr['stc'], hdr['stamps'] = stc

        return hdr

    def return_dat(self, chan, begsam, endsam):
        """TODO: prepare functions
        1. read stc for the content of the folder
        2. loop over erd and concatenate them

        it should allow for random access to the files, otherwise it's too slow
        to read the complete recording.

        """

        if isinstance(chan, int):
            chan = [chan]

        stc, all_stamp = _read_stc(join(self.filename, self._basename +
                                        '.stc'))

        all_erd = [x['segment_name'] for x in all_stamp]
        all_samples = [x['sample_span'] for x in all_stamp]
        n_sam_rec = concatenate((array([0]), cumsum(all_samples)))

        begrec = where(n_sam_rec <= begsam)[0][-1]
        endrec = where(n_sam_rec < endsam)[0][-1]

        dat = zeros((len(chan), endsam - begsam))
        d1 = 0
        for rec in range(begrec, endrec + 1):
            if rec == begrec:
                begpos_rec = begsam - n_sam_rec[rec]
            else:
                begpos_rec = 0

            if rec == endrec:
                endpos_rec = endsam - n_sam_rec[rec]
            else:
                endpos_rec = n_sam_rec[rec] + 1

            d2 = endpos_rec - begpos_rec + d1

            erd_file = join(self.filename, all_erd[rec] + '.erd')
            info(erd_file)
            dat_rec = _read_erd(erd_file, endpos_rec)
            dat[:, d1:d2] = dat_rec[chan, begpos_rec:endpos_rec]

            d1 = d2

        return dat

    def return_hdr(self):
        """Return the header for further use.

        Returns
        -------
        subj_id : str
            subject identification code
        start_time : datetime
            start time of the dataset
        s_freq : float
            sampling frequency
        chan_name : list of str
            list of all the channels
        n_samples : int
            number of samples in the dataset
        orig : dict
            additional information taken directly from the header

        Notes
        -----
        TODO:
            add real channel names

        """

        orig = self._hdr['erd']
        if orig['patient_id']:
            subj_id = orig['patient_id']
        else:
            subj_id = (orig['pat_first_name'] + orig['pat_middle_name'] +
                       orig['pat_last_name'])

        start_time = orig['creation_time']
        s_freq = orig['sample_freq']

        chan_name = ['chan{0:002d}'.format(ch)
                     for ch in range(orig['num_channels'])]
        n_samples = sum([x['sample_span'] for x in self._hdr['stamps']])

        try:
            orig['notes'] = self._read_notes()
        except IOError:
            orig['notes'] = 'could not find .ent file'
        return subj_id, start_time, s_freq, chan_name, n_samples, orig

    def _read_notes(self):
        """Reads the notes of the Ktlx recordings.

        However, this function formats the note already in the EDFBrowser
        format. Maybe the format should be more general.
        """
        ent_file = join(self.filename, self._basename + '.ent')

        ent_notes = _read_ent(ent_file)
        allnote = []
        for n in ent_notes:
            allnote.append(n['value'])

        s_freq = self._hdr['erd']['sample_freq']
        start_time = self._hdr['erd']['creation_time']
        pcname = '0CFEBE72-DA20-4b3a-A8AC-CDD41BFE2F0D'
        note_time = []
        note_name = []
        note_note = []
        for n in allnote:
            if n['Text'] == 'Analyzed Data Note':
                continue
            if not n['Text']:
                continue
            if 'User' not in n['Data'].keys():
                continue
            user1 = n['Data']['User'] == 'Persyst'
            user2 = n['Data']['User'] == 'eeg'
            user3 = n['Data']['User'] == pcname
            user4 = n['Data']['User'] == 'XLSpike - Intracranial'
            user5 = n['Data']['User'] == 'XLEvent - Intracranial'
            if user1 or user2 or user3 or user4 or user5:
                continue
            if len(n['Data']['User']) == 0:
                note_name.append('-unknown-')
            else:
                note_name.append(n['Data']['User'].split()[0])
            note_time.append(start_time +
                             timedelta(seconds=n['Stamp'] / s_freq))
            note_note.append(n['Text'])

        s = []
        for time, name, note in zip(note_time, note_name, note_note):
            s.append(datetime.strftime(time, '%Y-%m-%dT%H:%M:%S') +
                     ',' + '0' + ',' +  # zero duration
                     note + ' (' + name + ')')

        return '\n'.join(s)


if __name__ == "__main__":
    k = Ktlx('/home/gio/tools/read_xltek/MG59')
    dat = k.return_dat(10, 200000, 207000)
