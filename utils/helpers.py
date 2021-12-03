import texttable as tt

class helpers(object):
    def __init__ (self, local_salt_client):
        self.local_salt_client = local_salt_client

    def start_iperf_between_hosts(self, global_results, node_i, node_j, ip_i, ip_j, net_name):
        result = []
        direct_raw_results = self.start_iperf_client(node_i, ip_j)
        result.append(direct_raw_results)
        print("1 forward")
        forward = "1 thread:\n"
        forward += direct_raw_results + " Gbits/sec"

        direct_raw_results = self.start_iperf_client(node_i, ip_j, 10)
        result.append(direct_raw_results)
        print("10 forward")
        forward += "\n\n10 thread:\n"
        forward += direct_raw_results + " Gbits/sec"

        reverse_raw_results = self.start_iperf_client(node_j, ip_i)
        result.append(reverse_raw_results)
        print("1 backward")
        backward = "1 thread:\n"
        backward += reverse_raw_results + " Gbits/sec"

        reverse_raw_results = self.start_iperf_client(node_j, ip_i, 10)
        result.append(reverse_raw_results)
        print("10 backward")
        backward += "\n\n10 thread:\n"
        backward += reverse_raw_results + " Gbits/sec"
        global_results.append([node_i, node_j,
                               net_name, forward, backward])

        self.kill_iperf_processes(node_i)
        self.kill_iperf_processes(node_j)
        return result

    def draw_table_with_results(self, global_results):
        tab = tt.Texttable()
        header = [
            'node name 1',
            'node name 2',
            'network',
            'bandwidth >',
            'bandwidth <',
        ]
        tab.set_cols_align(['l', 'l', 'l', 'l', 'l'])
        tab.set_cols_width([27, 27, 15, 20, '20'])
        tab.header(header)
        for row in global_results:
            tab.add_row(row)
        s = tab.draw()
        print(s)

    def start_iperf_client(self, minion_name, target_ip, thread_count=None):
        iperf_command = 'timeout --kill-after=20 19 iperf -c {0}'.format(target_ip)
        if thread_count:
            iperf_command += ' -P {0}'.format(thread_count)
        output = self.local_salt_client.cmd(tgt=minion_name,
                                            fun='cmd.run',
                                            param=[iperf_command])
        # self.kill_iperf_processes(minion_name)
        try:
            result = output.values()[0].split('\n')[-1].split(' ')[-2:]
            if result[1] == 'Mbits/sec':
                return str(float(result[0])*0.001)
            if result[1] != 'Gbits/sec':
                return "0"
            return result[0]
        except:
            print("No iperf result between {} and {} (maybe they don't have "
                  "connectivity)".format(minion_name, target_ip))


    def kill_iperf_processes(self, minion_name):
        kill_command = "for pid in $(pgrep  iperf); do kill $pid; done"
        output = self.local_salt_client.cmd(tgt=minion_name,
                                            fun='cmd.run',
                                            param=[kill_command])
