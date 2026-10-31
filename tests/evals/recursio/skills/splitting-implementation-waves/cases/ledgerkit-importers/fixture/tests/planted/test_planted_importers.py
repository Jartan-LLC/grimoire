"""Planted acceptance tests: one basic file per format, a round trip per format, and load()."""

import pathlib
import tempfile
import unittest
from datetime import date
from decimal import Decimal

from ledgerkit import Transaction
from ledgerkit.importers import FORMATS, camt053, load, mt940, ofx, qif

QIF = """!Type:Bank
D03/01/2026
T-3.50
PCafe Uno
^
D3/ 2'26
T1,200.00
PSalary
N1001
^
"""

OFX = """OFXHEADER:100
DATA:OFXSGML
VERSION:102

<OFX>
<BANKMSGSRSV1><STMTTRNRS><STMTRS>
<CURDEF>USD
<BANKTRANLIST>
<STMTTRN>
<TRNTYPE>DEBIT
<DTPOSTED>20260301120000.000[-5:EST]
<TRNAMT>-3.50
<FITID>A1
<NAME>Cafe &amp; Bar
</STMTTRN>
<STMTTRN>
<TRNTYPE>DEBIT
<DTPOSTED>20260302
<TRNAMT>-3.50
<FITID>A1
<NAME>Cafe &amp; Bar
</STMTTRN>
</BANKTRANLIST>
</STMTRS></STMTTRNRS></BANKMSGSRSV1>
</OFX>
"""

MT940 = """:20:STMT1
:25:DE44500105175407324931
:28C:1/1
:60F:C260301EUR100,00
:61:2603010301D3,50NTRFNONREF//B1
:86:166?00KARTENZAHLUNG?20Coffee?21 morning?32Cafe Uno
:61:260302C1200,NTRFSAL-03
:86:Salary March/ACME GmbH
:62F:C260302EUR1296,50
-
:20:STMT2
:60F:C260302EUR1296,50
:61:260303D10,00NTRFNONREF
:62F:C260303EUR1290,00
-
"""

CAMT = """<?xml version="1.0" encoding="UTF-8"?>
<Document xmlns="urn:iso:std:iso:20022:tech:xsd:camt.053.001.08">
  <BkToCstmrStmt>
    <Stmt>
      <Ntry>
        <Amt Ccy="EUR">3.50</Amt>
        <CdtDbtInd>DBIT</CdtDbtInd>
        <Sts><Cd>BOOK</Cd></Sts>
        <BookgDt><Dt>2026-03-01</Dt></BookgDt>
        <NtryDtls><TxDtls>
          <Refs><EndToEndId>E2E-1</EndToEndId></Refs>
          <RltdPties><Cdtr><Pty><Nm>Cafe Uno</Nm></Pty></Cdtr></RltdPties>
          <RmtInf><Ustrd>Coffee</Ustrd><Ustrd>morning</Ustrd></RmtInf>
        </TxDtls></NtryDtls>
      </Ntry>
      <Ntry>
        <Amt Ccy="EUR">300.00</Amt>
        <CdtDbtInd>CRDT</CdtDbtInd>
        <Sts><Cd>BOOK</Cd></Sts>
        <BookgDt><DtTm>2026-03-02T09:15:00+01:00</DtTm></BookgDt>
        <AcctSvcrRef>BATCH-7</AcctSvcrRef>
        <NtryDtls>
          <TxDtls><Amt Ccy="EUR">100.00</Amt><RltdPties><Dbtr><Pty><Nm>Ann</Nm></Pty></Dbtr></RltdPties></TxDtls>
          <TxDtls><Amt Ccy="EUR">200.00</Amt><Refs><EndToEndId>E2E-9</EndToEndId></Refs><RltdPties><Dbtr><Pty><Nm>Bob</Nm></Pty></Dbtr></RltdPties></TxDtls>
        </NtryDtls>
      </Ntry>
      <Ntry>
        <Amt Ccy="EUR">9.99</Amt>
        <CdtDbtInd>DBIT</CdtDbtInd>
        <Sts><Cd>PDNG</Cd></Sts>
        <BookgDt><Dt>2026-03-03</Dt></BookgDt>
      </Ntry>
    </Stmt>
  </BkToCstmrStmt>
</Document>
"""

ROUND = [
    Transaction(date(2026, 3, 1), Decimal("-3.50"), "Cafe Uno", "Coffee", ref="R1"),
    Transaction(date(2026, 3, 2), Decimal("1200.00"), "ACME GmbH", "", ref="SAL-03"),
]


class PlantedTest(unittest.TestCase):
    def test_formats_registered(self):
        assert {"qif", "ofx", "mt940", "camt053"} <= set(FORMATS)

    def test_qif_basic(self):
        r = qif.parse(QIF)
        assert [(t.day, t.amount, t.payee) for t in r.transactions] == [
            (date(2026, 3, 1), Decimal("-3.50"), "Cafe Uno"),
            (date(2026, 3, 2), Decimal("1200.00"), "Salary"),
        ]
        assert r.transactions[1].ref == "1001"
        assert r.skipped == []

    def test_ofx_sgml_with_duplicate(self):
        r = ofx.parse(OFX)
        assert len(r.transactions) == 1
        t = r.transactions[0]
        assert (t.day, t.amount, t.payee, t.ref, t.currency) == (
            date(2026, 3, 1), Decimal("-3.50"), "Cafe & Bar", "A1", "USD"
        )
        assert len(r.skipped) == 1
        assert r.skipped[0].line == 16
        assert "duplicate" in r.skipped[0].reason

    def test_mt940_structured_plain_and_balance(self):
        r = mt940.parse(MT940)
        got = [(t.day, t.amount, t.payee, t.memo, t.ref, t.currency) for t in r.transactions]
        assert got == [
            (date(2026, 3, 1), Decimal("-3.50"), "Cafe Uno", "Coffee morning", None, "EUR"),
            (date(2026, 3, 2), Decimal("1200"), "Salary March", "ACME GmbH", "SAL-03", "EUR"),
        ]
        assert [(s.line, s.reason) for s in r.skipped] == [(11, "balance mismatch")]

    def test_load_sniffs_each_format(self):
        with tempfile.TemporaryDirectory() as tmp:
            for name, text, count in (("a.qif", QIF, 2), ("b.ofx", OFX, 1), ("c.sta", MT940, 2), ("d.xml", CAMT, 3)):
                p = pathlib.Path(tmp) / name
                p.write_text(text, encoding="utf-8")
                assert len(load(p).transactions) == count

    def test_camt053_batch_reference_and_pending(self):
        r = camt053.parse(CAMT)
        got = [(t.day, t.amount, t.payee, t.memo, t.ref, t.currency) for t in r.transactions]
        assert got == [
            (date(2026, 3, 1), Decimal("-3.50"), "Cafe Uno", "Coffee morning", "E2E-1", "EUR"),
            (date(2026, 3, 2), Decimal("100.00"), "Ann", "", "BATCH-7", "EUR"),
            (date(2026, 3, 2), Decimal("200.00"), "Bob", "", "E2E-9", "EUR"),
        ]
        assert [(s.line, s.reason) for s in r.skipped] == [(27, "pending")]

    def test_round_trip_every_format(self):
        assert qif.parse(qif.dump(ROUND)).transactions == ROUND
        assert ofx.parse(ofx.dump(ROUND)).transactions == ROUND
        assert mt940.parse(mt940.dump(ROUND, "DE44500105175407324931")).transactions == ROUND
        assert camt053.parse(camt053.dump(ROUND)).transactions == ROUND
