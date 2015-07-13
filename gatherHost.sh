#!/bin/bash
# Author: Ryan Xu (ID: 70320)
# Create time: 2013-11-7
# Copyrights@Asiainfo C3

echo_info()
{
  echo -e "$*"
}

# ##############################################
# 函数名： monitor_cpuinfo
# 入参：
# 返回：Succes:0, error: 1
# 函数功能：监控主机CPU性能数据
# 监控数据项：核数、系统占用CPU、用户占用CPU、
#             1分负载、5分负载、15分负载
# ##############################################
monitor_cpuinfo()
{
  cpu_num=`grep -c "model name" /proc/cpuinfo`
  
  loadavg1=`cat /proc/loadavg | awk '{ print $1 }'`
  loadavg5=`cat /proc/loadavg | awk '{ print $2 }'`
  loadavg15=`cat /proc/loadavg | awk '{ print $3 }'`
  
  #mpstat -P ALL | sed '1,2d' | awk '{ print $3"\t"$4"\t"$6 }'
  cpu_stat=`top -b -n 1 | grep Cpu | cut -d: -f2`
  cpu_user=`echo $cpu_stat | awk -F, '{ print $1 }' | cut -d% -f1 | awk '{printf("%.2f", $1)}'`
  cpu_sys=`echo $cpu_stat | awk -F, '{ print $2 }' | cut -d% -f1 | awk '{printf("%.2f", $1)}'`
  
  
  echo_info "host_cpu_cores_number@@@${cpu_num}###host_load_average_1@@@${loadavg1}###\
host_load_average_5@@@${loadavg5}###host_load_average_15@@@${loadavg15}###\
host_cpu_user_used@@@${cpu_user}###host_cpu_sys_used@@@${cpu_sys}"

}

# ##############################################
# 函数名： monitor_meminfo
# 入参：
# 返回：Succes:0, error: 1
# 函数功能：监控主机内存性能数据
# ##############################################
monitor_meminfo()
{
  MEMSIZE=`free -b|grep -i mem|awk '{print $2}'`
  USEDMEM=`free -b|grep -i mem|awk '{print $3}'`
  FREEMEM=`free -b|grep -i mem|awk '{print $4}'`
  memusedPercent=`echo "${USEDMEM} ${MEMSIZE}"|awk '{printf("%.2f",$1/$2)}'`
  SWAPSIZE=`free -b|grep -i swap|awk '{print $2}'`
  USEDSWAP=`free -b|grep -i swap|awk '{print $3}'`
  userUSEDMEM=`free -b|grep '^-/+'|awk '{print $3}'`
  userFREEMEM=`free -b|grep '^-/+'|awk '{print $4}'`
  
  echo_info "host_total_mem@@@${MEMSIZE}###host_free_mem@@@${FREEMEM}###\
host_percent_used_mem@@@${memusedPercent}###host_total_swap@@@${SWAPSIZE}###\
host_used_swap@@@${USEDSWAP}###host_free_mem(-/+)@@@${userFREEMEM}###\
host_used_mem(-/+)@@@${userUSEDMEM}"

}


# ##############################################
# 函数名： monitor_diskinfo
# 入参：
# 返回：Succes:0, error: 1
# 函数功能：监控主机磁盘空间数据
# ##############################################
monitor_diskinfo()
{
  # totalinfo=`df -k --total | tail -1`
  # total_all=`echo $totalinfo | awk '{ print $2 }'`
  # total_free=`echo $totalinfo | awk '{ print $4 }'`
  # total_used=`echo $totalinfo | awk '{ print $3 }'`
  # use_percent=`echo $totalinfo | awk '{ print $5 }'`
  eval $(df -k | sed '1d' | awk '{ t_all+=$2; t_used+=$3; t_free+=$4; useper=t_used/t_all} \
  END{ printf("total_all=%d total_used=%d total_free=%d use_percent=%.2f", t_all*1024, t_used*1024, t_free*1024, useper) }')
  
  total_regu=`ls -lR / 2>/dev/null | sed '1d'| awk '{print $1}' | grep -c '^[^d]'`
  total_dir=`ls -lR / 2>/dev/null | sed '1d'| awk '{print $1}' | grep -c '^d'`
  
  echo_info "total_disk@@@${total_all}###free_disk@@@${total_free}###\
used_disk@@@${total_used}###percent_used@@@${use_percent}###\
file_nums@@@${total_regu}###directory_nums@@@${total_dir}"

}

# ##############################################
# 函数名： monitor_workdir
# 入参：
# 返回：Succes:0, error: 1
# 函数功能：监控主机/export/home空间数据
# ##############################################
monitor_workdir()
{
  eval $(df -k /export/home | awk '{ t_all=$2; t_used=$3; t_free=$4; } \
  END{ printf("total_all=%d total_used=%d total_free=%d use_percent=%.2f", t_all*1024, t_used*1024, t_free*1024, t_used/t_all*100) }')
  
  echo_info "host_main_dir_path@@@/export/home###host_free_disk@@@${total_free}###\
host_total_disk@@@${total_all}###host_used_disk@@@${total_used}###\
host_disk_percent_used@@@${use_percent}"
}

calc_netspeed()
{
  face=$1
  i=0
  
  lastin_byte=0
  lastout_byte=0
  thisin_byte=0
  thisout_byte=0
  
  lastin_packet=0
  lastout_packet=0
  thisin_packet=0
  thisout_packet=0

  while [ 1 = 1 ]
  do
    ethinfo=`cat /proc/net/dev | grep $face | awk -F: '{ print $2 }'`
    thisin_byte=`echo $ethinfo|awk '{print $1}'`
    thisout_byte=`echo $ethinfo|awk '{print $9}'`
    thisin_packet=`echo $ethinfo|awk '{print $2}'`
    thisout_packet=`echo $ethinfo|awk '{print $10}'`
    
    if [ $i = 1 ]; then
      cin_byte=`expr $thisin_byte - $lastin_byte`
      cout_byte=`expr $thisout_byte - $lastout_byte`
      din_byte=`expr $cin_byte \* 8`
      dou_byte=`expr $cout_byte \* 8`
      ein_byte=`expr $din_byte / 10240`
      eout_byte=`expr $dou_byte / 10240`
      
      cin_packet=`expr $thisin_packet - $lastin_packet`
      cout_packet=`expr $thisout_packet - $lastout_packet`
      ein_packet=`expr $cin_packet / 10`
      eout_packet=`expr $cout_packet / 10`
      
      NETINFO=${NETINFO}"${face}_host_receive_kbps@@@${ein_byte}###${face}_host_transmit_kbps@@@${eout_byte}###\
${face}_host_receive_packet_speed@@@${ein_packet}###${face}_host_transmit_packet_speed@@@${eout_packet}|||"

      
      break #保证只统计一次
    fi
    lastin_byte=$thisin_byte
    lastout_byte=$thisout_byte
    
    lastin_packet=$thisin_packet
    lastout_packet=$thisout_packet
    
    i=1
    sleep 10
  done
}

# ##############################################
# 函数名： monitor_netcard
# 入参：
# 返回：Succes:0, error: 1
# 函数功能：监控主机网卡速度
# ##############################################
monitor_netcard()
{
  for face in `cat /proc/net/dev | sed '1,2d' |grep -v lo| grep -v sit |awk -F: '{ print $1 }'`
  #for face in `cat /proc/net/dev | sed '1,2d'|awk '{ print $1 }'|sed 's/://g'`
  do
    calc_netspeed $face
  done
  netinfo_len=`expr ${#NETINFO} - 3`
  NETINFO=`echo $NETINFO|cut -c1-${netinfo_len}`
  echo_info "${NETINFO}"
}


# ##############################################
# 函数名： pack_xmlmsg
# 入参：
# 返回：Succes:0, error: 1
# 函数功能：封装xml格式消息
# ##############################################
pack_xmlmsg()
{
  GATHER_TYPE=$*
  HOSTIPADDR=`hostname -i`
  HOSTNAME=`hostname`
  TIMESTAMP=`date +%s`
  
  echo_info "<d>
  <m k="hostip">${HOSTIPADDR}</m>
  <m k="hostname">${HOSTNAME}</m>
  <m k="gatherTime">${TIMESTAMP}</m>"
  
  $GATHER_TYPE
  
  echo_info "</d>"
  
}


# #########################################################################
# main 程序主执行接口
# #########################################################################
main()
{
  if [ $# -ne 1 ] || [ $1 = "help" ]; then
    echo "Usage: `basename $0` device"
    echo "device: [cpuinfo | diskinfo | meminfo | netinfo | all | help]"
    echo "eg: `basename $0` cpuinfo"
    exit 1
  fi
  
  if [ "x-$1" != "x-cpuinfo" ] && [ "x-$1" != "x-diskinfo" ] \
     && [ "x-$1" != "x-meminfo" ] && [ "x-$1" != "x-netinfo" ] \
     && [ "x-$1" != "x-all" ]; then
    echo "Usage: `basename $0` device"
    echo "device: [cpuinfo | diskinfo | meminfo | netinfo | all | help]"
    echo "eg: `basename $0` cpuinfo"
    exit 1
  fi
  
  DEVICE=$1
  
  case $DEVICE in
  cpuinfo) monitor_cpuinfo
  ;;
  diskinfo) monitor_workdir
  ;;
  meminfo) monitor_meminfo
  ;;
  netinfo) monitor_netcard
  ;;
  all)
  monitor_cpuinfo
  monitor_workdir
  monitor_meminfo
  monitor_netcard
  esac
  
  if [ $? != 0 ]; then
    echo "Gather host information failed, \
    please check the system running environment."
    exit 1
  fi

}

# start here
main $*