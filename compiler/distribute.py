import subprocess

def distribute(source_fname, target_fname):
    subprocess.call(['/home/weit/scotch/build/bin/gmap',
    'workspace/%s_source.txt'%source_fname,
    'workspace/%s_target.txt'%target_fname,
    'workspace/%s_output.txt'%target_fname])