import subprocess
import select

class MPlayer:
    def __init__(self):
        self.mplayer_instance = subprocess.Popen(['mplayer', '-slave', '-idle', '-quiet', '-nolirc'],
                                stdin=subprocess.PIPE, stdout=subprocess.PIPE, text=True)
        self._get_mplayer_command()

    def _get_output(self):
        output = list()
        while any(select.select([self.mplayer_instance.stdout.fileno()], [], [], 1.5)):
            output.append(self.mplayer_instance.stdout.readline())
        return output

    def _function_factory(self, cmd_name):
        def _generated_function(self, args=''):
            mplayer_input = cmd_name + ' ' + str(args) + '\n'
            self.mplayer_instance.stdin.write(mplayer_input)
            self.mplayer_instance.stdin.flush()
            output = self._get_output()
            return output
        return _generated_function

    def _get_mplayer_command(self):
        '''Collect output of `mplayer -input cmdlist` and generate function to `MPlayer` object'''
        _mplayer_cmdlist = subprocess.run(['mplayer', '-input', 'cmdlist'], capture_output=True, text=True)
        # Only get the command and add to list - setattr will call function factory to generate function
        cmdlist = list()
        for i in _mplayer_cmdlist.stdout.split('\n'):
            if i:
                cmdlist.append(i.split()[0])
        for i in cmdlist:
            setattr(MPlayer, i, self._function_factory(i))
