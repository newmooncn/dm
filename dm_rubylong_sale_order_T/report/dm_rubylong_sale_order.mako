<html xmlns="http://www.w3.org/1999/xhtml">
<head>
    <title>网页打印</title>
    <meta http-equiv="Content-Type" content="text/html; charset=utf-8"/>
    <script src="/dm_rubylong/static/CreateControl.js" type="text/javascript"></script>
    <script src="/dm_rubylong/static/GRInstall.js" type="text/javascript"></script>
    <script type="text/javascript">
        function window_onload() {
            ReportViewer.Stop();
            var Report = ReportViewer.Report;
            var Recordset = Report.DetailGrid.Recordset;
            //单头信息
            var fld_order_id_name = Report.FieldByName("order_id_name");//单据编号
            var fld_order_id_date_order = Report.FieldByName("order_id_date_order");//单据日期
            var fld_order_id_shop_id_name = Report.FieldByName("order_id_shop_id_name");//商店
            var fld_order_id_client_order_ref = Report.FieldByName("order_id_client_order_ref");//对方编号
            var fld_order_id_partner_id_name = Report.FieldByName("order_id_partner_id_name");//客户名称
            var fld_order_id_partner_id_parent_id_name = Report.FieldByName("order_id_partner_id_parent_id_name");//客户名称
            var fld_order_id_partner_id_parent_id_phone = Report.FieldByName("order_id_partner_id_parent_id_phone");//客户电话
            var fld_order_id_partner_id_parent_id_fax = Report.FieldByName("order_id_partner_id_parent_id_fax");//客户传真

            var fld_order_id_partner_id_street = Report.FieldByName("order_id_partner_id_street");//客户地址
            var fld_order_id_partner_id_phone = Report.FieldByName("order_id_partner_id_phone");//客户电话
            var fld_order_id_partner_id_fax = Report.FieldByName("order_id_partner_id_fax");//客户传真

            var fld_order_id_partner_id_mobile = Report.FieldByName("order_id_partner_id_mobile");//客户手机
            var fld_order_id_partner_id_user_name = Report.FieldByName("order_id_partner_id_user_name");//客户业务员

            var fld_order_id_company_id_street = Report.FieldByName("order_id_company_id_street");//公司地址
            var fld_order_id_company_id_emaile = Report.FieldByName("order_id_company_id_email");//公司邮箱

            var fld_order_id_partner_invoice_id_name = Report.FieldByName("order_id_partner_invoice_id_name");//发票地址
            var fld_order_id_partner_shipping_id_name = Report.FieldByName("order_id_partner_shipping_id_name");//送货地址
            var fld_order_id_user_id_name = Report.FieldByName("order_id_user_id_name");//销售员
            var fld_order_id_order_id_user_id_name_mobile = Report.FieldByName("order_id_user_id_name_mobile");//销售员联系手机


            var fld_order_id_company_id_name = Report.FieldByName("order_id_company_id_name");//所属公司
            var fld_order_id_company_id_phone = Report.FieldByName("order_id_company_id_phone");//所属公司电话
            var fld_order_id_company_id_fax = Report.FieldByName("order_id_company_id_fax");//所属公司传真
            var fld_order_id_amount_untaxed = Report.FieldByName("order_id_amount_untaxed");//不含税金额
            var fld_order_id_amount_tax = Report.FieldByName("order_id_amount_tax");//税额
            var fld_order_id_amount_total = Report.FieldByName("order_id_amount_total");//合计

            var fld_order_id_payment_term = Report.FieldByName("order_id_payment_term");//付款方式
            //var fld_order_id_order_id_delivery_time = Report.FieldByName("order_id_delivery_time");//交货时间

            ////单身信息
            var fld_line_product_id_default_code = Report.FieldByName("line_product_id_default_code");//产品编号
            var fld_line_product_id_name = Report.FieldByName("line_product_id_name");//产品名称
            var fld_line_product_id_variants = Report.FieldByName("line_product_id_variants");//产品规格
            var fld_line_product_uom_qty = Report.FieldByName("line_product_uom_qty");//产品数量
            var fld_line_product_uom_name = Report.FieldByName("line_product_uom_name");//单位
            var fld_line_price_unit = Report.FieldByName("line_price_unit");//单价
            var fld_line_discount = Report.FieldByName("line_discount");//折扣
            var fld_line_tax_id = Report.FieldByName("line_tax_id");//税率
            var fld_line_price_subtotal = Report.FieldByName("line_price_subtotal");
            var fld_line_note = Report.FieldByName("line_note");//备注

            var fld_line_line_material = Report.FieldByName("line_material");//材质
            var fld_line_line_weight_net = Report.FieldByName("line_weight_net");//净重(KG)
            var fld_line_line_weight_net_subtotal = Report.FieldByName("line_weight_net_subtotal");//总重(KG)
            Report.PrepareRecordset();
            //网页中的表格
            var tb_dm = document.getElementById("dm_table");
            var Rows = tb_dm.tBodies[0].rows;
            //将每行表格数据填入到报表记录集
            for (var i = 0; i < Rows.length; i++) {
                Recordset.Append();
                //FireFox不认innerText，只认textContent,所以这里要特殊处理
                if (Rows[i].cells[0].innerText) {
                    //单头信息
                    fld_order_id_name.Value = Rows[i].cells['order_id_name'].innerText; //innerHTML  Rows[i].cells[0].firstChild.nodeValue;
                    fld_order_id_date_order.Value = Rows[i].cells['order_id_date_order'].innerText;//
                    fld_order_id_shop_id_name.Value = Rows[i].cells['order_id_shop_id_name'].innerText;//
                    fld_order_id_partner_id_name.Value = Rows[i].cells['order_id_partner_id_name'].innerText;//
                    fld_order_id_partner_id_parent_id_name.Value = Rows[i].cells['order_id_partner_id_parent_id_name'].innerText;//
                    fld_order_id_partner_id_parent_id_phone.Value = Rows[i].cells['order_id_partner_id_parent_id_phone'].innerText;//
                    fld_order_id_partner_id_parent_id_fax.Value = Rows[i].cells['order_id_partner_id_parent_id_fax'].innerText;//

                    fld_order_id_partner_id_phone.Value = Rows[i].cells['order_id_partner_id_phone'].innerText;//
                    fld_order_id_partner_id_fax.Value = Rows[i].cells['order_id_partner_id_fax'].innerText;//
                    fld_order_id_client_order_ref.Value = Rows[i].cells['order_id_client_order_ref'].innerText;//
                    fld_order_id_partner_invoice_id_name.Value = Rows[i].cells['order_id_partner_invoice_id_name'].innerText;//
                    fld_order_id_partner_shipping_id_name.Value = Rows[i].cells['order_id_partner_shipping_id_name'].innerText;//
                    fld_order_id_user_id_name.Value = Rows[i].cells['order_id_user_id_name'].innerText;//
                    fld_order_id_order_id_user_id_name_mobile.Value = Rows[i].cells['order_id_user_id_name_mobile'].innerText;//

                    fld_order_id_partner_id_mobile.Value = Rows[i].cells['order_id_partner_id_mobile'].innerText;//
                    fld_order_id_partner_id_user_name.Value = Rows[i].cells['order_id_partner_id_user_name'].innerText;//
                    fld_order_id_company_id_street.Value = Rows[i].cells['order_id_company_id_street'].innerText;//
                    fld_order_id_company_id_emaile.Value = Rows[i].cells['order_id_company_id_email'].innerText;//

                    fld_order_id_company_id_name.Value = Rows[i].cells['order_id_company_id_name'].innerText;//
                    fld_order_id_company_id_phone.Value = Rows[i].cells['order_id_company_id_phone'].innerText;//
                    fld_order_id_company_id_fax.Value = Rows[i].cells['order_id_company_id_fax'].innerText;//
                    fld_order_id_amount_untaxed.Value = Rows[i].cells['order_id_amount_untaxed'].innerText;//
                    fld_order_id_amount_tax.Value = Rows[i].cells['order_id_amount_tax'].innerText;//
                    fld_order_id_amount_total.Value = Rows[i].cells['order_id_amount_total'].innerText;//
                    fld_order_id_payment_term.Value = Rows[i].cells['order_id_payment_term'].innerText;//
                    //fld_order_id_order_id_delivery_time.Value = Rows[i].cells['order_id_delivery_time'].innerText;//
                    fld_line_note.Value = Rows[i].cells['line_note'].innerText;//


                    ////单身信息
                    fld_line_product_id_default_code.Value = Rows[i].cells['line_product_id_default_code'].innerText;//
                    fld_line_product_id_name.Value = Rows[i].cells['line_product_id_name'].innerText;//
                    fld_line_product_id_variants.Value = Rows[i].cells['line_product_id_variants'].innerText;//
                    fld_line_product_uom_qty.Value = Rows[i].cells['line_product_uom_qty'].innerText;//
                    fld_line_product_uom_name.Value = Rows[i].cells['line_product_uom_name'].innerText;//
                    fld_line_price_unit.Value = Rows[i].cells['line_price_unit'].innerText;//
                    fld_line_discount.Value = Rows[i].cells['line_discount'].innerText;//
                    fld_line_tax_id.Value = Rows[i].cells['line_tax_id'].innerText;//
                    fld_line_price_subtotal.Value = Rows[i].cells['line_price_subtotal'].textContent;//
                    fld_order_id_partner_id_street.Value = Rows[i].cells['order_id_partner_id_street'].innerText;//

                    fld_line_line_material.Value = Rows[i].cells['line_material'].innerText;//
                    fld_line_line_weight_net.Value = Rows[i].cells['line_weight_net'].innerText;//
                    fld_line_line_weight_net_subtotal.Value = Rows[i].cells['line_weight_net_subtotal'].innerText;//


                }
                else {
                    //for firefox
                    //单头信息
                     fld_order_id_name.Value = Rows[i].cells['order_id_name'].textContent; //textContentHTML  Rows[i].cells[0].firstChild.nodeValue;
                    fld_order_id_date_order.Value = Rows[i].cells['order_id_date_order'].textContent;//
                    fld_order_id_shop_id_name.Value = Rows[i].cells['order_id_shop_id_name'].textContent;//
                    fld_order_id_partner_id_name.Value = Rows[i].cells['order_id_partner_id_name'].textContent;//
                    fld_order_id_partner_id_parent_id_name.Value = Rows[i].cells['order_id_partner_id_parent_id_name'].textContent;//
                    fld_order_id_partner_id_parent_id_phone.Value = Rows[i].cells['order_id_partner_id_parent_id_phone'].textContent;//
                    fld_order_id_partner_id_parent_id_fax.Value = Rows[i].cells['order_id_partner_id_parent_id_fax'].textContent;//

                    fld_order_id_partner_id_phone.Value = Rows[i].cells['order_id_partner_id_phone'].textContent;//
                    fld_order_id_partner_id_fax.Value = Rows[i].cells['order_id_partner_id_fax'].textContent;//
                    fld_order_id_client_order_ref.Value = Rows[i].cells['order_id_client_order_ref'].textContent;//
                    fld_order_id_partner_invoice_id_name.Value = Rows[i].cells['order_id_partner_invoice_id_name'].textContent;//
                    fld_order_id_partner_shipping_id_name.Value = Rows[i].cells['order_id_partner_shipping_id_name'].textContent;//
                    fld_order_id_user_id_name.Value = Rows[i].cells['order_id_user_id_name'].textContent;//
                    fld_order_id_order_id_user_id_name_mobile.Value = Rows[i].cells['order_id_user_id_name_mobile'].textContent;//

                    fld_order_id_partner_id_mobile.Value = Rows[i].cells['order_id_partner_id_mobile'].textContent;//
                    fld_order_id_partner_id_user_name.Value = Rows[i].cells['order_id_partner_id_user_name'].textContent;//
                    fld_order_id_company_id_street.Value = Rows[i].cells['order_id_company_id_street'].textContent;//
                    fld_order_id_company_id_emaile.Value = Rows[i].cells['order_id_company_id_email'].textContent;//

                    fld_order_id_company_id_name.Value = Rows[i].cells['order_id_company_id_name'].textContent;//
                    fld_order_id_company_id_phone.Value = Rows[i].cells['order_id_company_id_phone'].textContent;//
                    fld_order_id_company_id_fax.Value = Rows[i].cells['order_id_company_id_fax'].textContent;//
                    fld_order_id_amount_untaxed.Value = Rows[i].cells['order_id_amount_untaxed'].textContent;//
                    fld_order_id_amount_tax.Value = Rows[i].cells['order_id_amount_tax'].textContent;//
                    fld_order_id_amount_total.Value = Rows[i].cells['order_id_amount_total'].textContent;//
                    fld_order_id_payment_term.Value = Rows[i].cells['order_id_payment_term'].textContent;//
                    //fld_order_id_order_id_delivery_time.Value = Rows[i].cells['order_id_delivery_time'].textContent;//
                    fld_line_note.Value = Rows[i].cells['line_note'].textContent;//
                    ////单身信息
                    fld_line_product_id_default_code.Value = Rows[i].cells['line_product_id_default_code'].textContent;//
                    fld_line_product_id_name.Value = Rows[i].cells['line_product_id_name'].textContent;//
                    fld_line_product_id_variants.Value = Rows[i].cells['line_product_id_variants'].textContent;//
                    fld_line_product_uom_qty.Value = Rows[i].cells['line_product_uom_qty'].textContent;//
                    fld_line_product_uom_name.Value = Rows[i].cells['line_product_uom_name'].textContent;//
                    fld_line_price_unit.Value = Rows[i].cells['line_price_unit'].textContent;//
                    fld_line_discount.Value = Rows[i].cells['line_discount'].textContent;//
                    fld_line_tax_id.Value = Rows[i].cells['line_tax_id'].textContent;//
                    fld_line_price_subtotal.Value = Rows[i].cells['line_price_subtotal'].textContent;//
                    fld_order_id_partner_id_street.Value = Rows[i].cells['order_id_partner_id_street'].textContent;//

                    fld_line_line_material.Value = Rows[i].cells['line_material'].textContent;//
                    fld_line_line_weight_net.Value = Rows[i].cells['line_weight_net'].textContent;//
                    fld_line_line_weight_net_subtotal.Value = Rows[i].cells['line_weight_net_subtotal'].textContent;//

                }
                Recordset.Post();
            }
            ReportViewer.Start();      
        }
    </script>
    <style type="text/css">
        html, body {
            margin: 0;
            height: 100%;
        }
    </style>
</head>
<body onload="window_onload()">
<script type="text/javascript">
    CreatePrintViewerEx("100%", "100%", "/dm_rubylong_sale_order_T/static/dm_rubylong_sale_order.grf", "", false, "<param name=BorderStyle value=1>");
</script>
<div id="div" style="display: none">
    <table id="dm_table">
        % for o in objects:
            % for line in o.order_line:
                <tr>
                    <!--单头信息-->
                    <td id="order_id_name">${line.order_id.name  or ''}</td>
                    <td id="order_id_date_order">${line.order_id.date_order  or ''}</td>
                    <td id="order_id_shop_id_name">${line.order_id.shop_id.name  or ''}</td>
                    <td id="order_id_partner_id_name">${line.order_id.partner_id.name  or ''}</td>
                    <td id="order_id_partner_id_parent_id_name">${line.order_id.partner_id.parent_id.name  or line.order_id.partner_id.name  or ''}</td>
                    <td id="order_id_partner_id_parent_id_phone">${line.order_id.partner_id.parent_id.phone  or line.order_id.partner_id.phone  or ''}</td>
                    <td id="order_id_partner_id_parent_id_fax">${line.order_id.partner_id.parent_id.fax  or line.order_id.partner_id.fax or ''}</td>
                    <td id="order_id_client_order_ref">${line.order_id.client_order_ref  or ''}</td>
                    <td id="order_id_partner_invoice_id_name">${line.order_id.partner_invoice_id.name  or ''}</td>
                    <td id="order_id_partner_shipping_id_name">${line.order_id.partner_shipping_id.name  or ''}</td>
                    <td id="order_id_user_id_name">${line.order_id.user_id.name  or ''}</td>
                    <td id="order_id_user_id_name_mobile">${line.order_id.user_id.partner_id.mobile  or ''}</td>


                    <td id="order_id_company_id_name">${line.order_id.company_id.name  or ''}</td>
                    <td id="order_id_company_id_phone">${line.order_id.company_id.phone  or ''}</td>
                    <td id="order_id_company_id_fax">${line.order_id.company_id.fax  or ''}</td>
                    <td id="order_id_company_id_street">${line.order_id.company_id.street  or ''}</td>
                    <td id="order_id_company_id_email">${line.order_id.company_id.email  or ''}</td>

                    <td id="order_id_amount_untaxed">${line.order_id.amount_untaxed  or ''}</td>
                    <td id="order_id_amount_tax">${line.order_id.amount_tax  or ''}</td>
                    <td id="order_id_amount_total">${line.order_id.amount_total  or ''}</td>
                    <td id="order_id_payment_term">${line.order_id.payment_term.name  or ''}</td>
                    
                    <td id="order_id_partner_id_street">${line.order_id.partner_id.street  or ''}</td>
                    <td id="order_id_partner_id_phone">${line.order_id.partner_id.phone  or ''}</td>
                    <td id="order_id_partner_id_fax">${line.order_id.partner_id.fax  or ''}</td>
                    <td id="order_id_partner_id_mobile">${line.order_id.partner_id.mobile  or ''}</td>
                    <td id="order_id_partner_id_user_name">${line.order_id.partner_id.user_id.name  or ''}</td>

                    <!--单身信息-->
                    <td id="line_product_id_default_code">${line.product_id.default_code  or ''}</td>
                    <td id="line_product_id_name">${line.product_id.name  or ''}</td>
                    <td id="line_product_id_variants">${line.product_id.variants or ''}</td>
                    <td id="line_product_uom_qty">${line.product_uos and line.product_uos_qty or line.product_uom_qty  or ''}</td>
                    <td id="line_product_uom_name">${line.product_uos and line.product_uos.name or line.product_uom.name  or ''}</td>
                    <td id="line_price_unit">${line.price_unit  or ''}</td>
                    <td id="line_price_subtotal">${line.price_subtotal  or ''}</td>
                    <td id="line_discount">${line.discount  or ''}</td>
                    <td id="line_tax_id">${', '.join(map(lambda x: x.name, line.tax_id))}</td>
                    <td id="line_note">${line.order_id.note  or ''}</td>

                </tr>

            % endfor
        % endfor
    </table>
</div>
</body>
</html>
