"""
fabfile for deploying green-tracker demo.
"""

import os
from fabric.api import task, local, run, warn_only, settings, execute, env, cd
from fabric.operations import put
from fabric.contrib import files
import cliqz
import fabric.contrib as fcontrib

env.user = "ubuntu"
app_name = 'hpn-collector'
APP_ROOT = os.path.dirname(os.path.abspath(__file__))


@task
def config_dev_host():
    """config host for development"""
    cliqz.cli.prep_dev_host()


@task
def install_nginx(host_details=None):
    env.user = "ubuntu"
    version = '1.7.10.1'
    execute(run, "sudo apt-get install -y make libreadline-dev libncurses5-dev libpcre3-dev libssl-dev perl")
    #execute(run, "sudo useradd nginx")
    execute(run, "wget http://openresty.org/download/ngx_openresty-{}.tar.gz".format(version))
    execute(run, "tar -zxvf ngx_openresty-{}.tar.gz".format(version))
    execute(run, "sudo mkdir -p /opt/openresty/")
    execute(run, "cd ngx_openresty-{}/; sudo ./configure --prefix=/opt/openresty --with-luajit --with-http_iconv_module -j2; sudo make; sudo make install;".format(version))



@task()
def restart_nginx(host_details=None):
    env.user = "ubuntu"
    execute(run, 'cd /opt/openresty/nginx/;sudo /opt/openresty/nginx/sbin/nginx -s stop;sudo /opt/openresty/nginx/sbin/nginx')


@task()
def install_lua_openssl():
    env.user = "ubuntu"
    pkg = cliqz.package.gen_definition()
    files.upload_template('external_libs/lua-openssl.tar.gz', '/tmp/')
    #run("sudo ln -s /opt/openresty/luajit/bin/luajit-2.1.0-alpha /usr/bin/lua")
    run("sudo ln -s /opt/openresty/luajit/bin/luajit-2.1.0-alpha /usr/bin/lua")
    run("cd /tmp;tar -xvf lua-openssl.tar.gz; cd lua-openssl;sudo make;sudo make install")

@task()
def install_green_tracker():
    env.user = "ubuntu"


@task
def full_install(host_details=None):
    prepare_host()
    install_nginx()
    restart_nginx()
    install_deps()
    install_sourcemap()

@task
def prepare_host(host_details=None):
    env.user = "ubuntu"
    cliqz.cli.system_package('python-pip', 'gcc', 'make', 'python-dev', 'git',
                             'libevent-dev', 'emacs', 'htop', 'libxml2-dev',
                             'libxslt1-dev', 'libyaml-dev', 'libdb-dev', 'libz-dev',
                             'build-essential','pkg-config')


@task
def install_deps():
    env.user = "ubuntu"

    # Install utils.lua
    files.upload_template('../scripts/utils.lua', '/tmp/')
    run("cd /tmp;sudo cp utils.lua /opt/openresty/lualib/;")

@task
def install_sourcemap():
    env.user = "ubuntu"
    files.upload_template('../conf/sourcemap.json', '/tmp/')
    run("sudo mkdir -p /opt/openresty/nginx/html/sourcemaps/")
    run("cd /tmp;sudo cp sourcemap.json /opt/openresty/nginx/html/sourcemaps/;")


@task
def install_app():
    env.user = "ubuntu"

    base_dir = "/home/ubuntu/green-tracker"

    ##run("mkdir -p {}".format(base_dir))

    #f = ['server.py', 'report.py']
    #for f in files_list:
    #    files.upload_template('../conf/nginx.conf', base_dir)

    #import pdb
    #pdb.set_trace()
    #a=1

    ##put('./../src', '{}/src'.format(base_dir))

    run("mkdir -p {}".format(base_dir))
    run("mkdir -p {}".format('/mnt/logs'))




    #files.upload_template('../conf/nginx.conf', '{}/nginx.conf'.format(base_dir))

    put('../src/', '{}/src'.format(base_dir))


    #files.upload_template('../conf/nginx.conf', '/tmp/')
    #files.upload_template('../scripts/collector.lua', '/tmp/')
    #run("cd /tmp;sudo cp nginx.conf /opt/openresty/nginx/conf/;")
    #run("cd /tmp;sudo cp collector.lua /opt/openresty/nginx/;")
    #install_sourcemap()
    #restart_nginx()


### Misc stuff
@task
def update_owners():
    cliqz.host.install_keys(cliqz.get_config('project_owners'))

@task
def config_nginx(host_details=None):
    ctx = {
        'LOG': '/mnt/log/nginx_error.log',
        'CONFIG_VERSION': '0.03',
        'PORT': 6399,
        'CONF': '/opt/openresty/nginx/conf/nginx.conf',
    }

    execute(fcontrib.files.upload_template,
        deploy.APP_ROOT + '/conf/nginx.conf.tpl',
        ctx['CONF'],
        context=ctx)

    ##execute(restart_nginx)
    execute(run, '/opt/openresty/nginx/sbin/nginx -s stop; /opt/openresty/nginx/sbin/nginx')



def get_security_rules():
    return [
        {'ip_protocol': 'tcp',
         'from_port': 80,
         'to_port': 80,
         'cidr_ip': '0.0.0.0/0'},  # http
    ]


### Setup
cliqz.setup(
    app_name=app_name,
    project_owners=['josep, konark'],
    security_rules=get_security_rules(),
    policies=[
        {
            "Action": "route53:*",
            "Resource": "*",
            "Effect": "Allow",
        },
    ],
    cluster={
        'instances': [
            {'price_zone': 'c001',
             'spot_price': 0.7,
             'num_instances': 1,
             'instance_type': 'm3.xlarge',}
        ],
        'vpc_id': 'vpc-f0733595',
        'name': 'secureEventLogger',
        'primary_install': full_install,
     }
)