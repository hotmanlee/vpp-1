import os, fnmatch
import array
from hook import Hook

do_import = True
try:
    no_vpp_papi = os.getenv("NO_VPP_PAPI")
    if no_vpp_papi == "1":
        do_import = False
except:
    pass

if do_import:
    from vpp_papi import VPP

# from vnet/vnet/mpls/mpls_types.h
MPLS_IETF_MAX_LABEL = 0xfffff
MPLS_LABEL_INVALID = MPLS_IETF_MAX_LABEL + 1

class L2_VTR_OP:
    L2_POP_1 = 3

class VppPapiProvider(object):
    """VPP-api provider using vpp-papi

    @property hook: hook object providing before and after api/cli hooks


    """

    def __init__(self, name, shm_prefix, test_class):
        self.hook = Hook("vpp-papi-provider")
        self.name = name
        self.shm_prefix = shm_prefix
        self.test_class = test_class
        jsonfiles = []

        install_dir=os.getenv('VPP_TEST_INSTALL_PATH')
        for root, dirnames, filenames in os.walk(install_dir):
            for filename in fnmatch.filter(filenames, '*.api.json'):
                jsonfiles.append(os.path.join(root, filename))

        self.papi = VPP(jsonfiles)

    def register_hook(self, hook):
        """Replace hook registration with new hook

        :param hook:

        """
        self.hook = hook

    def connect(self):
        """Connect the API to VPP"""
        self.papi.connect(self.name, self.shm_prefix)

    def disconnect(self):
        """Disconnect the API from VPP"""
        self.papi.disconnect()

    def api(self, api_fn, api_args, expected_retval=0):
        """Call API function and check it's return value
        Call the appropriate hooks before and after the API call

        :param api_fn: API function to call
        :param api_args: tuple of API function arguments
        :param expected_retval: Expected return value (Default value = 0)
        :returns: reply from the API

        """
        self.hook.before_api(api_fn.__name__, api_args)
        reply = api_fn(**api_args)
        if hasattr(reply, 'retval') and reply.retval != expected_retval:
            msg = "API call failed, expected retval == %d, got %s" % (
                expected_retval, repr(reply))
            self.test_class.test_instance.logger.error(msg)
            raise Exception(msg)
        self.hook.after_api(api_fn.__name__, api_args)
        return reply

    def cli(self, cli):
        """
        Execute a CLI, calling the before/after hooks appropriately.

        :param cli: CLI to execute
        :returns: CLI output

        """
        self.hook.before_cli(cli)
        cli += '\n'
        r = self.papi.cli_inband(length=len(cli), cmd=cli)
        self.hook.after_cli(cli)
        if hasattr(r, 'reply'):
            return r.reply.decode().rstrip('\x00')

    def ppcli(self, cli):
        """
        Helping method to print CLI command in case of info logging level.

        :param cli: CLI to execute
        :returns: CLI output
        """
        return cli + "\n" + str(self.cli(cli))

    def _convert_mac(self, mac):
        return int(mac.replace(":", ""), 16) << 16

    def show_version(self):
        """ """
        return self.papi.show_version()

    def pg_create_interface(self, pg_index):
        """

        :param pg_index:

        """
        return self.api(self.papi.pg_create_interface,
                        { "interface_id" : pg_index })

    def sw_interface_dump(self, filter=None):
        """

        :param filter:  (Default value = None)

        """
        if filter is not None:
            args = {"name_filter_valid" : 1, "name_filter" : filter}
        else:
            args = {}
        return self.api(self.papi.sw_interface_dump, args)

    def sw_interface_set_table(self, sw_if_index, is_ipv6, table_id):
        """
          Set the IPvX Table-id for the Interface

        :param sw_if_index:
        :param is_ipv6:
        :param table_id:

        """
        return self.api(self.papi.sw_interface_set_table,
                        { 'sw_if_index' : sw_if_index, 'is_ipv6' : is_ipv6,
                          'vrf_id' : table_id})

    def sw_interface_add_del_address(self, sw_if_index, addr, addr_len,
                                     is_ipv6=0, is_add=1, del_all=0):
        """

        :param addr: param is_ipv6:  (Default value = 0)
        :param sw_if_index:
        :param addr_len:
        :param is_ipv6:  (Default value = 0)
        :param is_add:  (Default value = 1)
        :param del_all:  (Default value = 0)

        """
        return self.api(self.papi.sw_interface_add_del_address,
                        { 'sw_if_index' : sw_if_index,
                          'is_add' : is_add,
                          'is_ipv6' : is_ipv6,
                          'del_all' : del_all,
                          'address_length' : addr_len,
                          'address' : addr})

    def sw_interface_enable_disable_mpls(self, sw_if_index,
                                         is_enable=1):
        """
        Enable/Disable MPLS on the interface
        :param sw_if_index:
        :param is_enable:  (Default value = 1)

        """
        return self.api(self.papi.sw_interface_set_mpls_enable,
                        {'sw_if_index' : sw_if_index,
                         'enable' : is_enable })

    def sw_interface_ra_suppress(self, sw_if_index):
        return self.api(self.papi.sw_interface_ip6nd_ra_config,
                        {'sw_if_index' : sw_if_index })

    def vxlan_add_del_tunnel(
            self,
            src_addr,
            dst_addr,
            mcast_sw_if_index=0xFFFFFFFF,
            is_add=1,
            is_ipv6=0,
            encap_vrf_id=0,
            decap_next_index=0xFFFFFFFF,
            vni=0):
        """

        :param dst_addr:
        :param src_addr:
        :param is_add:  (Default value = 1)
        :param is_ipv6:  (Default value = 0)
        :param encap_vrf_id:  (Default value = 0)
        :param decap_next_index:  (Default value = 0xFFFFFFFF)
        :param mcast_sw_if_index:  (Default value = 0xFFFFFFFF)
        :param vni:  (Default value = 0)

        """
        return self.api(self.papi.vxlan_add_del_tunnel,
                        {'is_add' : is_add,
                         'is_ipv6' : is_ipv6,
                         'src_address' : src_addr,
                         'dst_address' : dst_addr,
                         'mcast_sw_if_index' : mcast_sw_if_index,
			 'encap_vrf_id' : encap_vrf_id,
                         'decap_next_index' : decap_next_index,
                         'vni' : vni})

    def bridge_domain_add_del(self, bd_id, flood=1, uu_flood=1, forward=1,
                              learn=1, arp_term=0, is_add=1):
        """Create/delete bridge domain.

        :param int bd_id: Bridge domain index.
        :param int flood: Enable/disable bcast/mcast flooding in the BD.
            (Default value = 1)
        :param int uu_flood: Enable/disable unknown unicast flood in the BD.
            (Default value = 1)
        :param int forward: Enable/disable forwarding on all interfaces in
            the BD. (Default value = 1)
        :param int learn: Enable/disable learning on all interfaces in the BD.
            (Default value = 1)
        :param int arp_term: Enable/disable arp termination in the BD.
            (Default value = 1)
        :param int is_add: Add or delete flag. (Default value = 1)
        """
        return self.api(self.papi.bridge_domain_add_del,
                        { 'bd_id' : bd_id,
                          'flood' : flood,
                          'uu_flood' : uu_flood,
                          'forward' : forward,
                          'learn' : learn,
                          'arp_term' : arp_term,
                          'is_add' : is_add})

    def l2fib_add_del(self, mac, bd_id, sw_if_index, is_add=1, static_mac=0,
                      filter_mac=0, bvi_mac=0):
        """Create/delete L2 FIB entry.

        :param str mac: MAC address to create FIB entry for.
        :param int bd_id: Bridge domain index.
        :param int sw_if_index: Software interface index of the interface.
        :param int is_add: Add or delete flag. (Default value = 1)
        :param int static_mac: Set to 1 to create static MAC entry.
            (Default value = 0)
        :param int filter_mac: Set to 1 to drop packet that's source or
            destination MAC address contains defined MAC address.
            (Default value = 0)
        :param int bvi_mac: Set to 1 to create entry that points to BVI
            interface. (Default value = 0)
        """
        return self.api(self.papi.l2fib_add_del,
                        { 'mac' : self._convert_mac(mac),
                          'bd_id' : bd_id,
                          'sw_if_index' : sw_if_index,
                          'is_add' : is_add,
                          'static_mac' : static_mac,
                          'filter_mac' : filter_mac,
                          'bvi_mac' : bvi_mac })

    def sw_interface_set_l2_bridge(self, sw_if_index, bd_id,
                                   shg=0, bvi=0, enable=1):
        """Add/remove interface to/from bridge domain.

        :param int sw_if_index: Software interface index of the interface.
        :param int bd_id: Bridge domain index.
        :param int shg: Split-horizon group index. (Default value = 0)
        :param int bvi: Set interface as a bridge group virtual interface.
            (Default value = 0)
        :param int enable: Add or remove interface. (Default value = 1)
        """
        return self.api(self.papi.sw_interface_set_l2_bridge,
                        { 'rx_sw_if_index' : sw_if_index,
                          'bd_id' : bd_id,
                          'shg' : shg,
                          'bvi' : bvi,
                          'enable' : enable })

    def bridge_flags(self, bd_id, is_set, feature_bitmap):
        """Enable/disable required feature of the bridge domain with defined ID.

        :param int bd_id: Bridge domain ID.
        :param int is_set: Set to 1 to enable, set to 0 to disable the feature.
        :param int feature_bitmap: Bitmap value of the feature to be set:
            - learn (1 << 0),
            - forward (1 << 1),
            - flood (1 << 2),
            - uu-flood (1 << 3) or
            - arp-term (1 << 4).
        """
        return self.api(self.papi.bridge_flags,
                        {'bd_id' : bd_id,
                         'is_set' : is_set,
                         'feature_bitmap' : feature_bitmap })

    def bridge_domain_dump(self, bd_id=0):
        """

        :param int bd_id: Bridge domain ID. (Default value = 0 => dump of all
            existing bridge domains returned)
        :return: Dictionary of bridge domain(s) data.
        """
        return self.api(self.papi.bridge_domain_dump,
                        {'bd_id' : bd_id })

    def sw_interface_set_l2_xconnect(self, rx_sw_if_index, tx_sw_if_index,
                                     enable):
        """Create or delete unidirectional cross-connect from Tx interface to
        Rx interface.

        :param int rx_sw_if_index: Software interface index of Rx interface.
        :param int tx_sw_if_index: Software interface index of Tx interface.
        :param int enable: Create cross-connect if equal to 1, delete
            cross-connect if equal to 0.

        """
        return self.api(self.papi.sw_interface_set_l2_xconnect,
                        { 'rx_sw_if_index' : rx_sw_if_index,
                          'tx_sw_if_index' : tx_sw_if_index,
                          'enable' : enable })

    def sw_interface_set_l2_tag_rewrite(self, sw_if_index, vtr_oper, push=0, tag1=0, tag2=0):
        """L2 interface vlan tag rewrite configure request
        :param client_index - opaque cookie to identify the sender
        :param context - sender context, to match reply w/ request
        :param sw_if_index - interface the operation is applied to
        :param vtr_op - Choose from l2_vtr_op_t enum values
        :param push_dot1q - first pushed flag dot1q id set, else dot1ad
        :param tag1 - Needed for any push or translate vtr op
        :param tag2 - Needed for any push 2 or translate x-2 vtr ops

        """
        return self.api(self.papi.l2_interface_vlan_tag_rewrite,
                        { 'sw_if_index' : sw_if_index,
                          'vtr_op' : vtr_oper,
                          'push_dot1q' : push,
                          'tag1' : tag1,
                          'tag2' : tag2 })

    def sw_interface_set_flags(self, sw_if_index, admin_up_down,
                               link_up_down=0, deleted=0):
        """

        :param admin_up_down:
        :param sw_if_index:
        :param link_up_down:  (Default value = 0)
        :param deleted:  (Default value = 0)

        """
        return self.api(self.papi.sw_interface_set_flags,
                        { 'sw_if_index' : sw_if_index,
                          'admin_up_down' : admin_up_down,
                          'link_up_down' : link_up_down,
                          'deleted' : deleted })

    def create_subif(self, sw_if_index, sub_id, outer_vlan, inner_vlan,
                     no_tags=0, one_tag=0, two_tags=0, dot1ad=0, exact_match=0,
                     default_sub=0, outer_vlan_id_any=0, inner_vlan_id_any=0):
        """Create subinterface
        from vpe.api: set dot1ad = 0 for dot1q, set dot1ad = 1 for dot1ad

        :param sub_id: param inner_vlan:
        :param sw_if_index:
        :param outer_vlan:
        :param inner_vlan:
        :param no_tags:  (Default value = 0)
        :param one_tag:  (Default value = 0)
        :param two_tags:  (Default value = 0)
        :param dot1ad:  (Default value = 0)
        :param exact_match:  (Default value = 0)
        :param default_sub:  (Default value = 0)
        :param outer_vlan_id_any:  (Default value = 0)
        :param inner_vlan_id_any:  (Default value = 0)

        """
        return self.api(
            self.papi.create_subif,
            { 'sw_if_index' : sw_if_index,
              'sub_id' : sub_id,
              'no_tags' : no_tags,
              'one_tag' : one_tag,
              'two_tags' : two_tags,
              'dot1ad' : dot1ad,
              'exact_match' : exact_match,
              'default_sub' : default_sub,
              'outer_vlan_id_any' : outer_vlan_id_any,
              'inner_vlan_id_any' : inner_vlan_id_any,
              'outer_vlan_id' : outer_vlan,
              'inner_vlan_id' : inner_vlan })

    def delete_subif(self, sw_if_index):
        """Delete subinterface

        :param sw_if_index:
        """
        return self.api(self.papi.delete_subif,
                        { 'sw_if_index' : sw_if_index })

    def create_vlan_subif(self, sw_if_index, vlan):
        """

        :param vlan:
        :param sw_if_index:

        """
        return self.api(self.papi.create_vlan_subif,
                        {'sw_if_index' : sw_if_index,
                         'vlan_id' : vlan })

    def create_loopback(self, mac=''):
        """

        :param mac: (Optional)
        """
        return self.api(self.papi.create_loopback,
                        { 'mac_address' : mac })

    def ip_add_del_route(
            self,
            dst_address,
            dst_address_length,
            next_hop_address,
            next_hop_sw_if_index=0xFFFFFFFF,
            table_id=0,
            next_hop_table_id=0,
            next_hop_weight=1,
            next_hop_n_out_labels = 0,
            next_hop_out_label_stack = [],
            next_hop_via_label = MPLS_LABEL_INVALID,
            create_vrf_if_needed=0,
            is_resolve_host=0,
            is_resolve_attached=0,
            classify_table_index=0xFFFFFFFF,
            is_add=1,
            is_drop=0,
            is_unreach=0,
            is_prohibit=0,
            is_ipv6=0,
            is_local=0,
            is_classify=0,
            is_multipath=0,
            not_last=0):
        """

        :param dst_address_length:
        :param next_hop_sw_if_index:  (Default value = 0xFFFFFFFF)
        :param dst_address:
        :param next_hop_address:
        :param next_hop_sw_if_index:  (Default value = 0xFFFFFFFF)
        :param vrf_id:  (Default value = 0)
        :param lookup_in_vrf:  (Default value = 0)
        :param classify_table_index:  (Default value = 0xFFFFFFFF)
        :param create_vrf_if_needed:  (Default value = 0)
        :param is_add:  (Default value = 1)
        :param is_drop:  (Default value = 0)
        :param is_ipv6:  (Default value = 0)
        :param is_local:  (Default value = 0)
        :param is_classify:  (Default value = 0)
        :param is_multipath:  (Default value = 0)
        :param is_resolve_host:  (Default value = 0)
        :param is_resolve_attached:  (Default value = 0)
        :param not_last:  (Default value = 0)
        :param next_hop_weight:  (Default value = 1)

        """

        return self.api(
            self.papi.ip_add_del_route,
            { 'next_hop_sw_if_index' : next_hop_sw_if_index,
              'table_id' : table_id,
              'classify_table_index' : classify_table_index,
              'next_hop_table_id' : next_hop_table_id,
              'create_vrf_if_needed' : create_vrf_if_needed,
              'is_add' : is_add,
              'is_drop' : is_drop,
              'is_unreach' : is_unreach,
              'is_prohibit' : is_prohibit,
              'is_ipv6' : is_ipv6,
              'is_local' : is_local,
              'is_classify' : is_classify,
              'is_multipath' : is_multipath,
              'is_resolve_host' : is_resolve_host,
              'is_resolve_attached' : is_resolve_attached,
              'not_last' : not_last,
              'next_hop_weight' : next_hop_weight,
              'dst_address_length' : dst_address_length,
              'dst_address' : dst_address,
              'next_hop_address' : next_hop_address,
              'next_hop_n_out_labels' : next_hop_n_out_labels,
              'next_hop_via_label' : next_hop_via_label,
              'next_hop_out_label_stack' : next_hop_out_label_stack })

    def ip_neighbor_add_del(self,
                            sw_if_index,
                            mac_address,
                            dst_address,
                            vrf_id=0,
                            is_add=1,
                            is_ipv6=0,
                            is_static=0,
                            ):
        """ Add neighbor MAC to IPv4 or IPv6 address.

        :param sw_if_index:
        :param mac_address:
        :param dst_address:
        :param vrf_id:  (Default value = 0)
        :param is_add:  (Default value = 1)
        :param is_ipv6:  (Default value = 0)
        :param is_static:  (Default value = 0)
        """

        return self.api(
            self.papi.ip_neighbor_add_del,
            { 'vrf_id' : vrf_id,
              'sw_if_index' : sw_if_index,
              'is_add' : is_add,
              'is_ipv6' : is_ipv6,
              'is_static' : is_static,
              'mac_address' : mac_address,
              'dst_address' : dst_address
             }
        )

    def sw_interface_span_enable_disable(
            self, sw_if_index_from, sw_if_index_to, enable=1):
        """

        :param sw_if_index_from:
        :param sw_if_index_to:
        :param enable

        """
        return self.api(self.papi.sw_interface_span_enable_disable,
                        { 'sw_if_index_from' : sw_if_index_from,
                          'sw_if_index_to' : sw_if_index_to,
                          'enable' : enable })

    def gre_tunnel_add_del(self,
                           src_address,
                           dst_address,
                           outer_fib_id=0,
                           is_teb=0,
                           is_add=1,
                           is_ip6=0):
        """ Add a GRE tunnel

        :param src_address:
        :param dst_address:
        :param outer_fib_id:  (Default value = 0)
        :param is_add:  (Default value = 1)
        :param is_ipv6:  (Default value = 0)
        :param is_teb:  (Default value = 0)
        """

        return self.api(
            self.papi.gre_add_del_tunnel,
            { 'is_add' : is_add,
              'is_ipv6' : is_ip6,
              'teb' : is_teb,
              'src_address' : src_address,
              'dst_address' : dst_address,
              'outer_fib_id' : outer_fib_id }
        )

    def mpls_route_add_del(
            self,
            label,
            eos,
            next_hop_proto_is_ip4,
            next_hop_address,
            next_hop_sw_if_index=0xFFFFFFFF,
            table_id=0,
            next_hop_table_id=0,
            next_hop_weight=1,
            next_hop_n_out_labels = 0,
            next_hop_out_label_stack = [],
            next_hop_via_label = MPLS_LABEL_INVALID,
            create_vrf_if_needed=0,
            is_resolve_host=0,
            is_resolve_attached=0,
            is_add=1,
            is_drop=0,
            is_multipath=0,
            classify_table_index=0xFFFFFFFF,
            is_classify=0,
            not_last=0):
        """

        :param dst_address_length:
        :param next_hop_sw_if_index:  (Default value = 0xFFFFFFFF)
        :param dst_address:
        :param next_hop_address:
        :param next_hop_sw_if_index:  (Default value = 0xFFFFFFFF)
        :param vrf_id:  (Default value = 0)
        :param lookup_in_vrf:  (Default value = 0)
        :param classify_table_index:  (Default value = 0xFFFFFFFF)
        :param create_vrf_if_needed:  (Default value = 0)
        :param is_add:  (Default value = 1)
        :param is_drop:  (Default value = 0)
        :param is_ipv6:  (Default value = 0)
        :param is_local:  (Default value = 0)
        :param is_classify:  (Default value = 0)
        :param is_multipath:  (Default value = 0)
        :param is_resolve_host:  (Default value = 0)
        :param is_resolve_attached:  (Default value = 0)
        :param not_last:  (Default value = 0)
        :param next_hop_weight:  (Default value = 1)

        """

        return self.api(
            self.papi.mpls_route_add_del,
            { 'mr_label' : label,
              'mr_eos' : eos,
              'mr_table_id' : table_id,
              'mr_classify_table_index' : classify_table_index,
              'mr_create_table_if_needed' : create_vrf_if_needed,
              'mr_is_add' : is_add,
              'mr_is_classify' : is_classify,
              'mr_is_multipath' : is_multipath,
              'mr_is_resolve_host' : is_resolve_host,
              'mr_is_resolve_attached' : is_resolve_attached,
              'mr_next_hop_proto_is_ip4' : next_hop_proto_is_ip4,
              'mr_next_hop_weight' : next_hop_weight,
              'mr_next_hop' : next_hop_address,
              'mr_next_hop_n_out_labels' : next_hop_n_out_labels,
              'mr_next_hop_sw_if_index' : next_hop_sw_if_index,
              'mr_next_hop_table_id' : next_hop_table_id,
              'mr_next_hop_via_label' : next_hop_via_label,
              'mr_next_hop_out_label_stack' : next_hop_out_label_stack })

    def mpls_ip_bind_unbind(
            self,
            label,
            dst_address,
            dst_address_length,
            table_id=0,
            ip_table_id=0,
            is_ip4=1,
            create_vrf_if_needed=0,
            is_bind=1):
        """
        """
        return self.api(
            self.papi.mpls_ip_bind_unbind,
            {'mb_mpls_table_id' : table_id,
             'mb_label' : label,
             'mb_ip_table_id' : ip_table_id,
             'mb_create_table_if_needed' : create_vrf_if_needed,
             'mb_is_bind' : is_bind,
             'mb_is_ip4' : is_ip4,
             'mb_address_length' : dst_address_length,
             'mb_address' : dst_address})

    def mpls_tunnel_add_del(
            self,
            tun_sw_if_index,
            next_hop_proto_is_ip4,
            next_hop_address,
            next_hop_sw_if_index=0xFFFFFFFF,
            next_hop_table_id=0,
            next_hop_weight=1,
            next_hop_n_out_labels = 0,
            next_hop_out_label_stack = [],
            next_hop_via_label = MPLS_LABEL_INVALID,
            create_vrf_if_needed=0,
            is_add=1,
            l2_only=0):
        """

        :param dst_address_length:
        :param next_hop_sw_if_index:  (Default value = 0xFFFFFFFF)
        :param dst_address:
        :param next_hop_address:
        :param next_hop_sw_if_index:  (Default value = 0xFFFFFFFF)
        :param vrf_id:  (Default value = 0)
        :param lookup_in_vrf:  (Default value = 0)
        :param classify_table_index:  (Default value = 0xFFFFFFFF)
        :param create_vrf_if_needed:  (Default value = 0)
        :param is_add:  (Default value = 1)
        :param is_drop:  (Default value = 0)
        :param is_ipv6:  (Default value = 0)
        :param is_local:  (Default value = 0)
        :param is_classify:  (Default value = 0)
        :param is_multipath:  (Default value = 0)
        :param is_resolve_host:  (Default value = 0)
        :param is_resolve_attached:  (Default value = 0)
        :param not_last:  (Default value = 0)
        :param next_hop_weight:  (Default value = 1)

        """
        return self.api(
            self.papi.mpls_tunnel_add_del,
            {'mt_sw_if_index' : tun_sw_if_index,
              'mt_is_add' : is_add,
              'mt_l2_only' : l2_only,
              'mt_next_hop_proto_is_ip4' : next_hop_proto_is_ip4,
              'mt_next_hop_weight' : next_hop_weight,
              'mt_next_hop' : next_hop_address,
              'mt_next_hop_n_out_labels' : next_hop_n_out_labels,
              'mt_next_hop_sw_if_index' :next_hop_sw_if_index,
              'mt_next_hop_table_id' : next_hop_table_id,
              'mt_next_hop_out_label_stack' : next_hop_out_label_stack })

        return self.api(vpp_papi.sw_interface_span_enable_disable,
                        (sw_if_index_from, sw_if_index_to, enable))
