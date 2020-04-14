import zipfile, os, sys, time
import paramiko


def make_zip(config):
    zipf = zipfile.ZipFile(config.zipFilePath, 'w')
    pre_len = len(os.path.dirname(config.basePath))
    for parent, dirnames, filenames in os.walk(config.basePath):
        if ".git" in parent:
            continue
        if "__pycache__" in parent:
            continue
        if parent.endswith("deploy"):
            continue
        if parent.endswith(".idea"):
            continue
        if parent.endswith("inspectionProfiles"):
            continue
        for filename in filenames:
            pathfile = os.path.join(parent, filename)
            arcname = pathfile[pre_len:].strip(os.path.sep)   #相对路径
            zipf.write(pathfile, arcname)
    zipf.close()


def open_ssh(config):
    '''
    创建ssh链接
    :param config:
    :return:
    '''
    s = paramiko.SSHClient()
    s.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    if config.option_type in ("account"):
        s.connect(hostname=config.ip, username=config.user, password=config.secret, port=config.port)
    else:
        s.load_system_host_keys()
        private_key = paramiko.RSAKey.from_private_key_file(config.secret)
        s.connect(hostname=config.ip, username=config.user, pkey=private_key, port=config.port)
    return s


def close_ssh(s):
    '''
    关闭ssh链接
    :param s:
    :return:
    '''
    s.close()


def ssh_cmd(s, cmd):
    '''
    ssh执行cmd
    :param s:
    :param config:
    :param cmd:
    :return:
    '''
    ssh_stdin, ssh_stdout, ssh_stderr = s.exec_command(cmd)
    print("output", ssh_stdout.read())
    error = ssh_stderr.read()
    print("err", error, len(error))


def ssh_put(s, config):
    '''
    ssh推送文件
    :param s:
    :param src_file:
    :param config:
    :return:
    '''
    sftp = s.open_sftp()
    sftp.put(config.zipFilePath, config.remove_path + config.zipfilename)
    sftp.close()

class Config:
    def __init__(self):
        self.absPath = sys.path[0]
        self.basePath = self.absPath[0:-7]
        self.zipfilename = "hbdm-client-%s.zip" % (time.strftime("%Y%m%d%H%M%S", time.localtime()))
        self.zipFilePath = os.path.join(self.absPath, self.zipfilename)
        self.ip = None
        self.user = None
        self.option_type = None
        self.secret = None
        self.remove_path = None
        self.port = None
        file = open("key", encoding='UTF-8')
        for line in file.readlines():
            if len(line) == 1:
                continue
            if line.startswith("#"):
                desc = line[1:]
                continue
            key_value = line.strip('\n').split("=")
            if hasattr(self, key_value[0]):
                setattr(self, key_value[0], key_value[1])


if __name__ == '__main__':
    config = Config()
    make_zip(config)
    print("压缩完毕")

    s = open_ssh(config)
    ssh_put(s, config)
    cmd = "cd %s; unzip -o %s; rm -rf %s;" %(config.remove_path, config.zipfilename, config.zipfilename)
    ssh_cmd(s, cmd)
    close_ssh(s)
    print("推送完毕")
