const {
  Document, Packer, Paragraph, TextRun, AlignmentType,
  HeadingLevel, PageNumber, NumberFormat, LevelFormat,
  TabStopType, TabStopPosition, UnderlineType, PageBreak
} = require('docx');
const fs = require('fs');

// ─── Shared helpers ────────────────────────────────────────────────────────

const font = "Times New Roman";
const sz = 24; // 12pt
const szSm = 20; // 10pt

function p(children, opts = {}) {
  return new Paragraph({
    children: Array.isArray(children) ? children : [children],
    spacing: { after: opts.after ?? 120, before: opts.before ?? 0 },
    alignment: opts.align ?? AlignmentType.LEFT,
    indent: opts.indent ? { left: opts.indent } : undefined,
    ...opts
  });
}

function t(text, opts = {}) {
  return new TextRun({ text, font, size: opts.sz ?? sz, bold: opts.bold, italics: opts.italic, underline: opts.underline ? { type: UnderlineType.SINGLE } : undefined });
}

function bold(text) { return t(text, { bold: true }); }
function italic(text) { return t(text, { italic: true }); }

function heading(text, level = 1) {
  return new Paragraph({
    children: [new TextRun({ text, font, size: sz, bold: true, underline: { type: UnderlineType.SINGLE } })],
    alignment: AlignmentType.CENTER,
    spacing: { before: 240, after: 120 }
  });
}

function subheading(text) {
  return new Paragraph({
    children: [new TextRun({ text, font, size: sz, bold: true })],
    spacing: { before: 200, after: 80 }
  });
}

function lineNum(num, content) {
  // California pleading paper style: line number + content
  return new Paragraph({
    children: [
      new TextRun({ text: `${String(num).padStart(2)} `, font, size: sz, color: "888888" }),
      ...( Array.isArray(content) ? content : [t(content)] )
    ],
    spacing: { after: 0, before: 0 },
    indent: { left: 720 }
  });
}

function blank() { return p([t("")], { after: 0 }); }

function caption(caseNum = "17D005687") {
  return [
    p([t("Savannah Baker", { bold: true })], { after: 0 }),
    p([t("5617 Marine Ave")], { after: 0 }),
    p([t("Twentynine Palms, CA 92277")], { after: 0 }),
    p([t("(949) 201-9245")], { after: 0 }),
    p([t("Savannahjbaker@gmail.com")], { after: 120 }),
    p([t("Respondent, In Pro Per")], { after: 360 }),
    p([bold("SUPERIOR COURT OF THE STATE OF CALIFORNIA")], { align: AlignmentType.CENTER, after: 0 }),
    p([bold("FOR THE COUNTY OF ORANGE")], { align: AlignmentType.CENTER, after: 240 }),
    // Case caption table-like layout
    p([t("MATHEW BAKER,"), t("                                Case No.: " + caseNum)], { after: 0 }),
    p([t("   Petitioner,")], { after: 0 }),
    blank(),
    p([t("vs.")], { after: 0 }),
    blank(),
    p([t("SAVANNAH BAKER,")], { after: 0 }),
    p([t("   Respondent.")], { after: 240 }),
  ];
}

// ══════════════════════════════════════════════════════════════════
// DOCUMENT 1: STRENGTHENED MOTION TO VACATE
// ══════════════════════════════════════════════════════════════════

function buildMotion() {
  const children = [
    ...caption(),
    p([bold("NOTICE OF MOTION AND MOTION TO VACATE CUSTODY ORDERS")], { align: AlignmentType.CENTER, after: 0 }),
    p([t("(Code Civ. Proc., § 473(d); Welf. & Inst. Code, § 302(d);")], { align: AlignmentType.CENTER, after: 0 }),
    p([t("Fam. Code, §§ 3409, 3422, 3044; Cal. Const. art. VI, § 21)")], { align: AlignmentType.CENTER, after: 240 }),
    p([t("DATE:   _______________")], { after: 0 }),
    p([t("TIME:   _______________")], { after: 0 }),
    p([t("DEPT:   _______________")], { after: 240 }),
    p([bold("TO ALL PARTIES AND THEIR ATTORNEYS OF RECORD:")], { align: AlignmentType.CENTER, after: 240 }),

    p([t("PLEASE TAKE NOTICE that on a date and time to be set by the Court, Respondent Savannah Baker will and hereby does move the Court for an order vacating the custody provisions of the December 14, 2023 minute order, and any derivative custody orders, on the following independent grounds:")], { after: 120 }),

    p([t("1. The December 14, 2023 custody order is "), bold("void for lack of subject-matter jurisdiction"), t(". The Superior Court, County of Orange, lacked authority to modify existing juvenile dependency exit orders without first conducting a proper jurisdictional analysis under the Uniform Child Custody Jurisdiction and Enforcement Act (UCCJEA), Family Code sections 3400–3465. The proceedings that gave rise to the December 14, 2023 order were initiated by a materially defective UCCJEA declaration that concealed the Orange County dissolution action (Case No. 17D005687), the juvenile dependency proceedings (Nos. 20DP1110; 20DP1111), and the operative custody orders. A court that acts without subject-matter jurisdiction renders a void order that may be challenged at any time. ("), italic("People v. American Contractors Indemnity Co."), t(" (2004) 33 Cal.4th 653, 660; Code Civ. Proc., § 473(d).)")], { after: 120 }),

    p([t("2. The December 14, 2023 order is "), bold("void or voidable under Welfare and Institutions Code section 302(d)"), t(". The custody provisions of the August 25, 2021 Custody Order—Juvenile—Final Judgment (form JV-200), affirmed on appeal in February 2022, constitute a final custody judgment that may not be modified unless the court finds (a) a significant change of circumstances since issuance of the exit orders, and (b) that modification is in the best interests of the children. The December 14, 2023 order contains no reference to section 302(d), no finding of significant change of circumstances, and no best-interests finding under that statute. (Welf. & Inst. Code, § 302(d); "), italic("Heidi S. v. David H."), t(" (2016) 1 Cal.App.5th 1150; Cal. Rules of Court, rule 5.700.)")], { after: 120 }),

    p([t("3. The December 14, 2023 order was entered by "), bold("Commissioner Thomas J. Lo without a valid written stipulation"), t(" of the parties as required by California Constitution, Article VI, section 21. Respondent, appearing in pro per at the December 14, 2023 hearing, never knowingly stipulated in writing to the commissioner's authority to act as a temporary judge and enter a binding final custody order. (Cal. Const., art. VI, § 21; "), italic("In re Marriage of Monge"), t(" (2001) 93 Cal.App.4th 911.)")], { after: 120 }),

    p([t("4. The December 14, 2023 order was entered in violation of "), bold("Family Code section 3044"), t(". Petitioner/Father has a 2017 Penal Code section 243(e)(1) conviction for domestic violence and a March 22, 2018 permanent restraining order, both judicially noticed at the December 14, 2023 hearing. The court took judicial notice of the restraining order yet made no finding under section 3044 and issued no written statement of the reasons required to overcome the statutory presumption against granting physical custody to a person who has committed domestic violence. (Fam. Code, § 3044; "), italic("In re Marriage of Fajota"), t(" (2014) 230 Cal.App.4th 1487, 1497–1498.)")], { after: 120 }),

    p([t("5. The proceedings leading to the December 14, 2023 order were tainted by "), bold("extrinsic fraud and material misrepresentation"), t(" by Petitioner's counsel, including: (a) presentation of a San Bernardino County minute order dated 8/24/22 that was entered without proper jurisdiction; (b) misrepresentation to the court that Petitioner was attending Alcoholics Anonymous meetings; and (c) a materially false UCCJEA declaration concealing the existence of this Orange County action and the juvenile exit orders. (CCP § 473(d); "), italic("Rappleyea v. Campbell"), t(" (1994) 8 Cal.4th 975.)")], { after: 120 }),

    p([t("6. The May 1, 2023 UCCJEA conference was conducted "), bold("without Respondent's participation"), t(", in violation of Respondent's due process rights. The resulting orders, and any orders premised upon them, were entered without affording Respondent a meaningful opportunity to be heard on jurisdictional questions that directly determined the forum and governing law for all subsequent proceedings.")], { after: 240 }),

    p([t("This motion is based on this Notice, the attached Memorandum of Points and Authorities, the Declaration of Savannah Baker, the Request for Judicial Notice, and all records and files in this action.")], { after: 240 }),

    p([t("Dated: _______________")], { after: 360 }),
    blank(),
    p([t("_________________________________")], { after: 0 }),
    p([bold("Savannah Baker")], { after: 0 }),
    p([t("Respondent, In Pro Per")], { after: 480 }),

    // ── MEMORANDUM ──────────────────────────────────────────────────
    new Paragraph({ children: [new PageBreak()] }),
    heading("MEMORANDUM OF POINTS AND AUTHORITIES"),

    subheading("I. INTRODUCTION"),
    p([t("This motion presents six independent, non-overlapping grounds to vacate the custody provisions of the December 14, 2023 minute order. Three of those grounds—lack of UCCJEA subject-matter jurisdiction, exclusion of Respondent from the UCCJEA conference, and extrinsic fraud—render the challenged order void ab initio, subject to challenge at any time with no time bar. The remaining grounds—failure to comply with Welfare and Institutions Code section 302(d), failure to apply the Family Code section 3044 domestic violence presumption, and entry of final orders by a commissioner without stipulation—render the order voidable. Any one of these grounds independently justifies vacatur.")], { after: 120 }),

    p([t("Respondent does not ask this Court to reweigh evidence or revisit discretionary determinations. The defects argued here are facial: they appear on the face of the December 14, 2023 order and the judicially noticeable record.")], { after: 240 }),

    subheading("II. FACTUAL AND PROCEDURAL BACKGROUND"),

    p([bold("A. The Juvenile Dependency Exit Orders (August 2021)")], { after: 80 }),
    p([t("In August 2021, the Orange County Juvenile Court terminated dependency jurisdiction over Rylin Baker (DOB 11/20/2011) and Scarlett Baker (DOB 3/26/2013) and issued a Custody Order—Juvenile—Final Judgment (form JV-200) pursuant to Welfare and Institutions Code section 302(d). That order, signed by the Honorable Jeremy Dolnick on August 25, 2021, awarded: joint legal custody to both parents; joint physical custody to both parents; and primary residence with Respondent/Mother Savannah J. Jochum Baker. (See Exhibit A to Request for Judicial Notice.)")], { after: 120 }),
    p([t("The juvenile court directed that the exit orders be transmitted to Riverside County Superior Court, where they were filed in family law case FLIN2102534 on September 29, 2021. (Exhibit A.) In February 2022, the Fourth District Court of Appeal affirmed the juvenile exit orders in their entirety, establishing their status as a final custody judgment subject to modification only in compliance with section 302(d). (Exhibit B.)")], { after: 120 }),

    p([bold("B. Petitioner's Defective New Filing in San Bernardino (May 2022)")], { after: 80 }),
    p([t("On May 24, 2022, Petitioner Mathew Baker filed a new custody action in San Bernardino County (Case No. FAMMB2200255). The UCCJEA declaration filed in support of that petition omitted: (1) the pending Orange County dissolution action (Case No. 17D005687), which had been active since 2015 and transferred to Orange County in 2017; (2) the juvenile dependency proceedings (Nos. 20DP1110; 20DP1111); and (3) the August 2021 exit orders and their appellate affirmance. This omission deprived San Bernardino of the information necessary to determine whether it had UCCJEA modification jurisdiction. (Fam. Code, § 3409.)")], { after: 120 }),

    p([bold("C. The May 1, 2023 UCCJEA Conference")], { after: 80 }),
    p([t("On May 1, 2023, a UCCJEA inter-judicial conference was conducted in San Bernardino (Barstow Division) among Commissioner James Bruce Minton, the Honorable Thomas J. Lo (Orange County), and the Honorable Susanne Cho (Riverside County). Respondent was not present and did not participate in the conference. The resulting minute order reflects that Judge Lo elected to retain venue in Orange County, Judge Cho declined jurisdiction and deferred to Orange County, and the Barstow Court concurred that the Orange County dissolution action had priority as the original venue county. The May 1, 2023 order also preserved San Bernardino Commissioner Minton's prior emergency orders. (Exhibit C.)")], { after: 120 }),

    p([bold("D. The December 14, 2023 Order")], { after: 80 }),
    p([t("On December 14, 2023, Commissioner Thomas J. Lo presided over a hearing in Orange County. Respondent appeared in pro per. At that hearing: (a) Petitioner's counsel presented the San Bernardino 8/24/22 minute order awarding Petitioner sole legal and sole physical custody—an order entered by a court that lacked modification jurisdiction; (b) Petitioner's counsel represented on the record that Petitioner was attending Alcoholics Anonymous meetings, which the Court accepted without verification; (c) Respondent requested that the juvenile dependency exit orders be reinstated; and (d) the Court stated only that the exit orders had 'subsequently been modified,' without identifying the statutory authority for that modification or making the findings required by section 302(d).")], { after: 120 }),
    p([t("The resulting minute order: awarded Petitioner/Father sole physical custody; ordered joint legal custody; set a parenting schedule designating Respondent to 1st, 3rd, and 5th weekends plus Wednesday dinners; and declared the orders 'final orders under "), italic("Montenegro v. Diaz"), t(", (2001) 26 Cal.4th 249.' The order contains no reference to Welfare and Institutions Code section 302(d), no finding of significant change of circumstances, and no written findings under Family Code section 3044 despite the court having taken judicial notice of the March 22, 2018 permanent restraining order. (Exhibit D.)")], { after: 240 }),

    subheading("III. LEGAL STANDARD"),

    p([bold("A. Code of Civil Procedure Section 473(d)")], { after: 80 }),
    p([t("Code of Civil Procedure section 473(d) provides that '[t]he court may ... set aside any void judgment or order.' A judgment or order is void when the court lacked fundamental jurisdiction—'an entire absence of power to hear or determine the case, an absence of authority over the subject matter or the parties.' ("), italic("People v. American Contractors Indemnity Co."), t(" (2004) 33 Cal.4th 653, 660.) A void order 'is vulnerable to direct or collateral attack at any time.' ("), italic("Id."), t(") There is no time limit on a motion to vacate a void order. ("), italic("California Capital Insurance Co. v. Hoehn"), t(" (2024) 17 Cal.5th 207.)")], { after: 120 }),

    p([bold("B. Void vs. Voidable")], { after: 80 }),
    p([t("An order entered where the court lacked subject-matter jurisdiction is void. An order entered where the court possessed jurisdiction but exceeded the authority conferred by statute is voidable. ("), italic("People v. Lara"), t(" (2010) 48 Cal.4th 216, 224.) The UCCJEA/subject-matter-jurisdiction defect argued in Section IV renders the December 14, 2023 order void. The section 302(d), section 3044, and commissioner-authority defects argued in Sections V–VII independently render the order voidable on its face.")], { after: 240 }),

    subheading("IV. THE DECEMBER 14, 2023 ORDER IS VOID FOR LACK OF UCCJEA SUBJECT-MATTER JURISDICTION"),

    p([bold("A. UCCJEA Jurisdiction Is Subject-Matter Jurisdiction That Cannot Be Conferred by Consent")], { after: 80 }),
    p([t("Under the UCCJEA, child custody jurisdiction is subject-matter jurisdiction. A California court may modify an existing child custody determination only if it has modification jurisdiction under Family Code section 3422 or section 3423. Section 3422 grants exclusive continuing jurisdiction (CEJ) to the court that made the initial custody determination; a second court may modify only if the first court has lost CEJ under the specific conditions set forth in section 3422(a).")], { after: 120 }),
    p([t("A court that modifies a custody determination without first establishing its modification jurisdiction exceeds its authority in a fundamental sense, rendering the resulting order void. Subject-matter jurisdiction cannot be conferred by the parties' consent, waiver, or failure to object. ("), italic("Lee v. An"), t(" (2008) 168 Cal.App.4th 558, 564–565.)")], { after: 120 }),

    p([bold("B. Petitioner's Defective UCCJEA Declaration Deprived San Bernardino of the Information Required to Assess Jurisdiction")], { after: 80 }),
    p([t("Family Code section 3429 requires each party in a custody proceeding to file a declaration disclosing all prior and pending custody proceedings involving the children. Petitioner's May 2022 UCCJEA declaration omitted this action (17D005687), the juvenile dependency proceedings, and the exit orders. This concealment prevented the San Bernardino court from conducting a proper UCCJEA jurisdictional analysis and from communicating with Orange County and Riverside County as required under section 3410.")], { after: 120 }),

    p([bold("C. The May 1, 2023 UCCJEA Conference Order Confirms Orange County's Priority Jurisdiction and Undermines the Validity of San Bernardino's Prior Orders")], { after: 80 }),
    p([t("The May 1, 2023 UCCJEA conference minute order expressly provides that: Orange County has priority as the original venue county; the Orange County dissolution action was still pending; and all future proceedings would be handled by Orange County. The same order characterizes the San Bernardino orders as 'emergency orders' only—not permanent modification orders. Emergency custody jurisdiction is a separate and limited grant of authority that does not authorize permanent custody modifications. (Fam. Code, § 3424.)")], { after: 120 }),
    p([t("Critically, the UCCJEA conference was conducted without Respondent's participation, violating her right to present facts and legal arguments before a jurisdictional determination was made. (Fam. Code, § 3410(b).)")], { after: 120 }),

    p([bold("D. The December 14, 2023 Order Relied on San Bernardino's Void 8/24/22 Order")], { after: 80 }),
    p([t("At the December 14, 2023 hearing, Petitioner's counsel presented and the Court considered the San Bernardino minute order of August 24, 2022, awarding Petitioner sole legal and sole physical custody. That order was entered after Petitioner filed a petition that concealed the existence of this action and the exit orders. San Bernardino lacked UCCJEA modification jurisdiction at the time—Orange County was the court of continuing exclusive jurisdiction. The December 14, 2023 order's reliance on a void antecedent order as though it were valid precedent independently demonstrates that it, too, was entered without a proper jurisdictional foundation.")], { after: 240 }),

    subheading("V. THE ORDER IS VOID OR VOIDABLE UNDER WELFARE AND INSTITUTIONS CODE SECTION 302(d)"),

    p([t("Welfare and Institutions Code section 302(d) provides that custody and visitation orders issued upon termination of dependency jurisdiction 'shall be a final judgment' and 'shall not be modified ... unless the court finds that there has been a significant change of circumstances since the juvenile court issued the order and modification of the order is in the best interests of the child.' Both findings are mandatory predicates to modification. ("), italic("Heidi S. v. David H."), t(" (2016) 1 Cal.App.5th 1150; Cal. Rules of Court, rule 5.700.)")], { after: 120 }),
    p([t("The December 14, 2023 order contains neither finding. The order acknowledges the existence of the juvenile exit orders and states they were 'subsequently modified,' but it neither cites section 302(d) nor contains any finding of significant change of circumstances or a best-interests determination under that statute. In the absence of the mandatory statutory predicates, the modification was entered in excess of statutory authority and is void or voidable under Code of Civil Procedure section 473(d).")], { after: 240 }),

    subheading("VI. THE ORDER VIOLATES FAMILY CODE SECTION 3044"),

    p([t("Family Code section 3044(a) creates a rebuttable presumption that granting sole or joint physical custody to a person who has perpetrated domestic violence within the preceding five years is detrimental to the best interest of the child. Section 3044(d) expressly provides that a Penal Code section 243(e)(1) conviction constitutes a finding of domestic violence for purposes of the presumption.")], { after: 120 }),
    p([t("At the December 14, 2023 hearing, the Court took judicial notice of the March 22, 2018 permanent restraining order issued after hearing against Petitioner. Petitioner's 2017 Penal Code section 243(e)(1) domestic violence conviction is part of the judicially noticeable record. Despite the existence of these domestic violence findings, the December 14, 2023 order awarded Petitioner sole physical custody with no written findings under section 3044 and no statement of the reasons required to overcome the statutory presumption. This failure is reversible error and supports vacatur. ("), italic("In re Marriage of Fajota"), t(" (2014) 230 Cal.App.4th 1487, 1497–1498.)")], { after: 240 }),

    subheading("VII. THE ORDER IS VOIDABLE BECAUSE IT WAS ENTERED BY A COMMISSIONER WITHOUT A VALID STIPULATION"),

    p([t("California Constitution, Article VI, section 21 provides that a court commissioner may act as a temporary judge only '[o]n stipulation of the parties litigant.' A written or knowing oral stipulation is required before a commissioner may enter binding final orders. ("), italic("In re Marriage of Monge"), t(" (2001) 93 Cal.App.4th 911, 917.)")], { after: 120 }),
    p([t("The December 14, 2023 hearing was presided over by Commissioner Thomas J. Lo. The minute order is styled 'Judge / Commissioner: THOMAS J. LO.' Respondent appeared in pro per and was not advised, and did not knowingly stipulate in writing, to Commissioner Lo's authority to enter binding final custody orders. In the absence of a valid stipulation, the December 14, 2023 order was entered without constitutional authority and is voidable.")], { after: 240 }),

    subheading("VIII. CONCLUSION"),

    p([t("The custody provisions of the December 14, 2023 minute order are void or voidable on their face for each of the independent grounds set forth above. The required statutory findings do not appear in the record. The underlying proceedings were initiated through concealment of this Court's priority jurisdiction. The orders were entered by a commissioner without valid stipulation. The domestic violence presumption was ignored. Respondent requests that this Court:")], { after: 120 }),
    p([t("1. Vacate the custody provisions of the December 14, 2023 minute order and any derivative custody orders;")], { indent: 720, after: 80 }),
    p([t("2. Declare that the Custody Order—Juvenile—Final Judgment (JV-200) issued August 25, 2021 by the Honorable Jeremy Dolnick and affirmed on appeal in February 2022 remains in full force and effect as the governing custody order, subject to modification only upon compliance with Welfare and Institutions Code section 302(d); and")], { indent: 720, after: 80 }),
    p([t("3. Grant such other and further relief as the Court deems just and proper.")], { indent: 720, after: 240 }),

    p([t("Dated: _______________")], { after: 360 }),
    blank(),
    p([t("_________________________________")], { after: 0 }),
    p([bold("Savannah Baker")], { after: 0 }),
    p([t("Respondent, In Pro Per")], { after: 0 }),
  ];

  return new Document({
    sections: [{ properties: { page: { size: { width: 12240, height: 15840 }, margin: { top: 1440, right: 1440, bottom: 1440, left: 1440 } } }, children }]
  });
}

// ══════════════════════════════════════════════════════════════════
// DOCUMENT 2: DECLARATION OF SAVANNAH BAKER
// ══════════════════════════════════════════════════════════════════

function buildDeclaration() {
  const children = [
    ...caption(),
    p([bold("DECLARATION OF SAVANNAH BAKER IN SUPPORT OF")], { align: AlignmentType.CENTER, after: 0 }),
    p([bold("MOTION TO VACATE CUSTODY ORDERS")], { align: AlignmentType.CENTER, after: 240 }),

    p([t("I, Savannah Baker, declare as follows:")], { after: 120 }),

    p([bold("Personal Background and Current Status")], { after: 80 }),
    p([t("1. I am the Respondent in the above-captioned action. I am the mother of Rylin Baker (born November 20, 2011) and Scarlett Baker (born March 26, 2013). I make this declaration based on my personal knowledge. If called as a witness, I could and would testify competently to the facts stated herein.")], { after: 120 }),
    p([t("2. I am currently representing myself in pro per. I have retained counsel at various points in this litigation but have been forced to proceed without counsel due to financial hardship.")], { after: 120 }),

    p([bold("The Juvenile Dependency Proceedings and Exit Orders")], { after: 80 }),
    p([t("3. In 2020, juvenile dependency proceedings were initiated in Orange County Superior Court under case numbers 20DP1110 and 20DP1111 involving Rylin and Scarlett.")], { after: 120 }),
    p([t("4. On August 25, 2021, the Honorable Jeremy Dolnick of the Orange County Juvenile Court terminated dependency jurisdiction and issued a Custody Order—Juvenile—Final Judgment (form JV-200). That order granted joint legal custody, joint physical custody, and established primary residence with me as the children's mother. A true and correct copy is attached as Exhibit A to the concurrently filed Request for Judicial Notice.")], { after: 120 }),
    p([t("5. The juvenile court directed the exit orders be transmitted to Riverside County, where they were lodged in case FLIN2102534 on September 29, 2021. An appeal of the exit orders was filed, and in February 2022, the Court of Appeal affirmed them. Since that affirmance, those orders have constituted a final custody judgment.")], { after: 120 }),

    p([bold("Petitioner's New San Bernardino Filing and UCCJEA Defects")], { after: 80 }),
    p([t("6. On or about May 24, 2022, Petitioner Mathew Baker filed a new custody action in San Bernardino County (FAMMB2200255). I have reviewed the UCCJEA declaration filed with that petition. It does not disclose the existence of this Orange County dissolution action (Case No. 17D005687), the juvenile dependency proceedings, or the August 2021 exit orders. These were existing custody proceedings and orders directly involving these children.")], { after: 120 }),
    p([t("7. Prior to the filing of that San Bernardino petition, my then-attorney Lauren Laundis had put Petitioner's counsel Jacob Plott on written notice, by letter dated September 29, 2022, that the juvenile court's exit orders directed that any modification must be brought in the family court case in which they were filed—in this case, Orange County. Despite this notice, proceedings continued in San Bernardino.")], { after: 120 }),
    p([t("8. On or about June 30, 2022, Petitioner's counsel stated on the record in the Joshua Tree court that it did not have jurisdiction over this matter. I was present and heard this statement. Nonetheless, subsequent proceedings continued in San Bernardino without proper jurisdictional authority.")], { after: 120 }),

    p([bold("The May 1, 2023 UCCJEA Conference — I Was Excluded")], { after: 80 }),
    p([t("9. On May 1, 2023, I was informed that a UCCJEA jurisdictional conference was being held in Barstow. I was not present at and did not participate in that conference. I was not given a meaningful opportunity to present facts or legal arguments to the three judges—Commissioner Minton, Judge Lo, and Judge Cho—before they made jurisdictional determinations that controlled all subsequent proceedings.")], { after: 120 }),
    p([t("10. The May 1, 2023 minute order states that 'Judge Lo chooses to retain venue in Orange County,' that Riverside County declines and defers to Orange County, and that the Barstow Court concurs that 'the dissolution action in Orange County is still pending and has priority.' Despite this confirmation that Orange County had priority jurisdiction, San Bernardino's prior emergency orders were preserved without my participation or consent.")], { after: 120 }),

    p([bold("The October 12, 2023 Hearing — Petitioner's Counsel Vouches for False Facts")], { after: 80 }),
    p([t("11. At the October 12, 2023 hearing before Commissioner Lo, Petitioner's counsel stated on the record that Petitioner had proof of attending Alcoholics Anonymous meetings on his phone. The Court accepted this representation and noted it in the minute order. To the best of my knowledge and belief, Petitioner has not consistently attended or completed an AA program. I was not given an adequate opportunity to challenge or verify this representation before the Court accepted it.")], { after: 120 }),

    p([bold("The December 14, 2023 Hearing — Key Facts")], { after: 80 }),
    p([t("12. On December 14, 2023, I appeared in pro per before Commissioner Thomas J. Lo. I was not represented by counsel.")], { after: 120 }),
    p([t("13. I was not advised by the Court at any point that Commissioner Lo was acting as a temporary judge rather than a judge, and I was not asked to stipulate, and did not stipulate in writing, to Commissioner Lo's authority to enter a final and binding custody order.")], { after: 120 }),
    p([t("14. During the hearing, I testified and requested that the Court reinstate the juvenile dependency exit orders from August 2021. The Court responded that those orders had 'subsequently been modified.' The Court did not identify the statutory basis for any prior modification, did not find that there had been a significant change of circumstances, and did not make best-interests findings under Welfare and Institutions Code section 302(d).")], { after: 120 }),
    p([t("15. Petitioner's counsel presented to the Court a San Bernardino County minute order dated August 24, 2022, which purported to award Petitioner sole legal and sole physical custody. I contend, and contended at the hearing, that this San Bernardino order was not validly obtained, as it was entered by a court that lacked jurisdiction to modify the juvenile exit orders and was based on a petition that concealed the existence of this Orange County action.")], { after: 120 }),
    p([t("16. At the December 14, 2023 hearing, the Court took judicial notice of the permanent restraining order issued against Petitioner on March 22, 2018, after a hearing. Petitioner has a prior criminal conviction for domestic violence under Penal Code section 243(e)(1) from 2017. Despite taking judicial notice of the restraining order, the Court made no findings under Family Code section 3044, did not apply the statutory presumption against granting physical custody to a person who has perpetrated domestic violence, and stated no reasons for overcoming that presumption.")], { after: 120 }),
    p([t("17. The December 14, 2023 order awarded Petitioner sole physical custody and designated me to 1st, 3rd, and 5th weekends and Wednesday dinner visits. This order has been actively enforced and has materially reduced my time with my children.")], { after: 120 }),

    p([bold("Ongoing Harm to the Children")], { after: 80 }),
    p([t("18. In December 2023, Scarlett was returned to me with a severe lice infestation. There were over ten live lice visible without parting her hair, hundreds of eggs including in her baby hairs and visible on her forehead, and a bloody scalp. Multiple live lice were found in her clothing. This condition was indicative of significant neglect during the time in Petitioner's care.")], { after: 120 }),
    p([t("19. Petitioner was arrested in the presence of the children. In 2025, Petitioner was arrested for domestic violence in front of the children. CPS became involved and temporary protective orders were issued. An investigation found domestic violence concerns.")], { after: 120 }),
    p([t("20. Scarlett has been suspended from school on multiple occasions for physical altercations. I believe these behavioral issues are related to instability and exposure to domestic violence in Petitioner's home.")], { after: 120 }),
    p([t("21. Mathew Baker regularly withheld the children on Wednesdays even removing them from school. This was addressed in court. The Orange County clerk and Judge Lo's court confirmed the Wednesday time was my parenting time under the operative order and did not require modification.")], { after: 120 }),

    p([bold("Diligence")], { after: 80 }),
    p([t("22. I have diligently pursued legal remedies throughout these proceedings. I have been impeded by financial inability to maintain consistent representation, by procedural complexity across three counties, and by the active misrepresentation and obstruction described above. I bring this motion promptly upon being able to research and identify the specific legal grounds described herein.")], { after: 240 }),

    p([t("I declare under penalty of perjury under the laws of the State of California that the foregoing is true and correct.")], { after: 240 }),

    p([t("Executed on _______________, 2025, at _______________, California.")], { after: 360 }),
    blank(),
    p([t("_________________________________")], { after: 0 }),
    p([bold("Savannah Baker")], { after: 0 }),
    p([t("Declarant")], { after: 0 }),
  ];

  return new Document({
    sections: [{ properties: { page: { size: { width: 12240, height: 15840 }, margin: { top: 1440, right: 1440, bottom: 1440, left: 1440 } } }, children }]
  });
}

// ══════════════════════════════════════════════════════════════════
// DOCUMENT 3: REQUEST FOR JUDICIAL NOTICE
// ══════════════════════════════════════════════════════════════════

function buildRJN() {
  const children = [
    ...caption(),
    p([bold("RESPONDENT'S REQUEST FOR JUDICIAL NOTICE")], { align: AlignmentType.CENTER, after: 0 }),
    p([bold("IN SUPPORT OF MOTION TO VACATE CUSTODY ORDERS")], { align: AlignmentType.CENTER, after: 0 }),
    p([t("(Evid. Code, §§ 452, 453)")], { align: AlignmentType.CENTER, after: 240 }),

    p([t("Respondent Savannah Baker hereby requests, pursuant to Evidence Code sections 452(c), 452(d), and 453, that this Court take judicial notice of the following documents, all of which are official records of courts of the State of California:")], { after: 240 }),

    p([bold("EXHIBIT A: Custody Order—Juvenile—Final Judgment (Form JV-200)")], { after: 80 }),
    p([t("True and correct copies of the following documents comprising the August 2021 juvenile exit orders:")], { after: 80 }),
    p([t("(a) JV-200 (Custody Order—Juvenile—Final Judgment), signed by the Honorable Jeremy Dolnick, dated August 25, 2021, Orange County Superior Court, case nos. 20DP1110 and 20DP1111, as lodged in Riverside County case FLIN2102534 and received September 29, 2021;")], { indent: 720, after: 80 }),
    p([t("(b) JV-205 (Visitation/Parenting Time Order—Juvenile), incorporated into the JV-200;")], { indent: 720, after: 80 }),
    p([t("(c) FL-341(C) (Children's Holiday Schedule Attachment), incorporated into the JV-200;")], { indent: 720, after: 120 }),
    p([t("These are official court records. (Evid. Code, § 452(d).)")], { after: 120 }),

    p([bold("EXHIBIT B: Court of Appeal Opinion Affirming Exit Orders (February 2022)")], { after: 80 }),
    p([t("A true and correct copy of the opinion of the California Court of Appeal, Fourth Appellate District, filed in February 2022, affirming the August 2021 juvenile exit orders. (Evid. Code, § 452(d).)")], { after: 120 }),

    p([bold("EXHIBIT C: May 1, 2023 UCCJEA Conference Minute Orders")], { after: 80 }),
    p([t("True and correct copies of:")], { after: 80 }),
    p([t("(a) The Portal Minute Order of the San Bernardino County Superior Court, Barstow District, dated May 1, 2023, case no. FAMMB2200255, documenting the UCCJEA conference among Commissioner James Bruce Minton, Judge Thomas J. Lo, and Judge Susanne Cho, and reflecting Judge Lo's retention of venue in Orange County, Judge Cho's declination of jurisdiction, and the Barstow Court's deference to Orange County;")], { indent: 720, after: 80 }),
    p([t("(b) The Orange County Superior Court Minute Order dated May 1, 2023, case no. 17D005687, signed by Judge Thomas J. Lo, ordering Orange County to be the proper venue and that any orders by Commissioner Minton of San Bernardino County shall remain in full force and effect.")], { indent: 720, after: 120 }),
    p([t("These are official court records. (Evid. Code, § 452(d).)")], { after: 120 }),

    p([bold("EXHIBIT D: December 14, 2023 Minute Order (The Challenged Order)")], { after: 80 }),
    p([t("A true and correct copy of the Orange County Superior Court Minute Order dated December 14, 2023, case no. 17D005687, presided over by Commissioner Thomas J. Lo, awarding Petitioner sole physical custody and entering the parenting schedule and additional orders described therein. (Evid. Code, § 452(d).)")], { after: 120 }),

    p([bold("EXHIBIT E: October 12, 2023 Minute Order (730 Status Hearing)")], { after: 80 }),
    p([t("A true and correct copy of the Orange County Superior Court Minute Order dated October 12, 2023, case no. 17D005687, reflecting: Commissioner Lo's acceptance of Petitioner's counsel's representation regarding AA attendance; the court's stated concerns about Respondent's credibility based on prior findings and UCCJEA conferences; and the continuance to December 14, 2023. (Evid. Code, § 452(d).)")], { after: 120 }),

    p([bold("EXHIBIT F: July 11, 2023 Minute Order")], { after: 80 }),
    p([t("A true and correct copy of the Orange County Superior Court Minute Order dated July 11, 2023, case no. 17D005687, ordering the 730 evaluation by stipulation of both parties (Leslie Drozd or another agreed evaluator), establishing temporary week-on/week-off summer schedule, and noting the 'previous finding of Respondent not credible.' (Evid. Code, § 452(d).)")], { after: 120 }),

    p([bold("EXHIBIT G: San Bernardino Minute Order Dated August 24, 2022")], { after: 80 }),
    p([t("A true and correct copy of the San Bernardino County Superior Court minute order dated August 24, 2022, presented to the Orange County court at the December 14, 2023 hearing by Petitioner's counsel, purporting to award Petitioner sole legal and sole physical custody. This is offered to show its contents and the circumstances of its presentation, not for the truth of its custody determinations. (Evid. Code, §§ 452(d), 453.)")], { after: 120 }),

    p([bold("EXHIBIT H: March 22, 2018 Permanent Restraining Order")], { after: 80 }),
    p([t("A true and correct copy of the permanent restraining order issued after hearing on March 22, 2018 against Petitioner Mathew Baker, judicially noticed at the December 14, 2023 hearing. This document reflects a judicial finding of domestic violence within the meaning of Family Code section 3044. (Evid. Code, §§ 452(d), 453.)")], { after: 120 }),

    p([bold("EXHIBIT I: September 29, 2022 Meet-and-Confer Letter from Attorney Lauren Laundis")], { after: 80 }),
    p([t("A true and correct copy of the letter dated September 29, 2022, from attorney Lauren Laundis (counsel for Respondent) to Jacob Plott, counsel for Petitioner, citing the JV-200 notice provision and advising that modification of the exit orders must be brought in the family court case in which they are filed. This letter is offered to establish that Petitioner's counsel was on written notice of the exit orders and the proper forum before the continuation of San Bernardino proceedings.")], { after: 240 }),

    p([bold("AUTHORITY")], { after: 80 }),
    p([t("Evidence Code section 452(d) permits judicial notice of '[r]ecords of any court of this state.' Evidence Code section 453 requires the court to take judicial notice of a matter specified in section 452 '[i]f a party requests it and ... [g]ives each adverse party sufficient notice of the request, through the pleadings or otherwise, to enable such adverse party to prepare to meet the request.'")], { after: 240 }),

    p([t("Dated: _______________")], { after: 360 }),
    blank(),
    p([t("_________________________________")], { after: 0 }),
    p([bold("Savannah Baker")], { after: 0 }),
    p([t("Respondent, In Pro Per")], { after: 0 }),
  ];

  return new Document({
    sections: [{ properties: { page: { size: { width: 12240, height: 15840 }, margin: { top: 1440, right: 1440, bottom: 1440, left: 1440 } } }, children }]
  });
}

// ══════════════════════════════════════════════════════════════════
// DOCUMENT 4: PROPOSED ORDER
// ══════════════════════════════════════════════════════════════════

function buildOrder() {
  const children = [
    ...caption(),
    p([bold("[PROPOSED] ORDER GRANTING MOTION TO VACATE CUSTODY ORDERS")], { align: AlignmentType.CENTER, after: 240 }),

    p([t("The above-captioned matter came before the Court on _______________, 2025, at _______ [a.m./p.m.] in Department _____ of the above-entitled Court. Respondent Savannah Baker appeared in pro per. Petitioner Mathew Baker appeared [through counsel / in person].")], { after: 120 }),
    p([t("The Court, having considered the Motion to Vacate Custody Orders, the Memorandum of Points and Authorities, the Declaration of Savannah Baker, the Request for Judicial Notice, all exhibits submitted therewith, and the oral argument of the parties, and having found good cause therefor, hereby ORDERS as follows:")], { after: 240 }),

    subheading("ORDERS"),

    p([bold("1. Vacatur of December 14, 2023 Custody Orders.")], { after: 80 }),
    p([t("The custody provisions of the December 14, 2023 Minute Order, Orange County Superior Court, Case No. 17D005687, including but not limited to the orders regarding physical custody, legal custody, parenting time, and holiday schedule, are hereby VACATED pursuant to Code of Civil Procedure section 473(d) on the ground that they are void/voidable for the following reason(s) (check all that apply):")], { indent: 720, after: 80 }),

    p([t("☐  Lack of UCCJEA subject-matter jurisdiction")], { indent: 1080, after: 40 }),
    p([t("☐  Failure to comply with Welfare and Institutions Code section 302(d)")], { indent: 1080, after: 40 }),
    p([t("☐  Entry by commissioner without valid stipulation (Cal. Const., art. VI, § 21)")], { indent: 1080, after: 40 }),
    p([t("☐  Failure to apply Family Code section 3044 domestic violence presumption")], { indent: 1080, after: 40 }),
    p([t("☐  Extrinsic fraud / material misrepresentation")], { indent: 1080, after: 40 }),
    p([t("☐  Denial of due process (exclusion from UCCJEA conference)")], { indent: 1080, after: 120 }),

    p([bold("2. Reinstatement of Juvenile Exit Orders.")], { after: 80 }),
    p([t("The Custody Order—Juvenile—Final Judgment (form JV-200) issued by the Honorable Jeremy Dolnick on August 25, 2021, in Orange County Superior Court, case nos. 20DP1110 and 20DP1111, as lodged in Riverside County case FLIN2102534, and as affirmed on appeal in February 2022, is hereby declared to be in full force and effect as the governing custody order for minor children Rylin Baker and Scarlett Baker.")], { indent: 720, after: 120 }),
    p([t("Pursuant to the reinstated JV-200 order: Respondent/Mother Savannah J. Jochum Baker shall have primary residence of the minor children; the parties shall share joint legal custody; and parenting time for Petitioner/Father shall be as provided in the accompanying JV-205 and FL-341(C).")], { indent: 720, after: 120 }),

    p([bold("3. Modification Standard.")], { after: 80 }),
    p([t("Any future modification of the reinstated juvenile exit orders shall be subject to Welfare and Institutions Code section 302(d). No order modifying the exit orders shall be entered without a finding of (a) a significant change of circumstances since issuance of the exit orders, and (b) that modification is in the best interests of the minor children.")], { indent: 720, after: 120 }),

    p([bold("4. Compliance with Family Code Section 3044.")], { after: 80 }),
    p([t("Before any further custody order awarding sole or joint physical custody to Petitioner is entered, this Court shall apply the presumption set forth in Family Code section 3044 and make the specific written findings required by that statute.")], { indent: 720, after: 120 }),

    p([bold("5. Further Orders.")], { after: 80 }),
    p([t("☐  The Court further orders: _________________________________________________")], { indent: 720, after: 120 }),
    p([t("☐  A further hearing is set for _______________, 2025, at _______ [a.m./p.m.] in Department _____.")], { indent: 720, after: 240 }),

    p([t("IT IS SO ORDERED.")], { after: 120 }),
    p([t("Date: _______________")], { after: 360 }),
    blank(),
    p([t("_________________________________")], { after: 0 }),
    p([bold("Judge / Commissioner, Orange County Superior Court")], { after: 0 }),
    p([t("Department _____")], { after: 0 }),
  ];

  return new Document({
    sections: [{ properties: { page: { size: { width: 12240, height: 15840 }, margin: { top: 1440, right: 1440, bottom: 1440, left: 1440 } } }, children }]
  });
}

// ── Write all four files ───────────────────────────────────────────

async function main() {
  const outDir = process.argv[2] || '/home/claude';
  const files = [
    { doc: buildMotion(), name: "01_Motion_to_Vacate.docx" },
    { doc: buildDeclaration(), name: "02_Declaration_Savannah_Baker.docx" },
    { doc: buildRJN(), name: "03_Request_for_Judicial_Notice.docx" },
    { doc: buildOrder(), name: "04_Proposed_Order.docx" },
  ];

  for (const { doc, name } of files) {
    const buf = await Packer.toBuffer(doc);
    fs.writeFileSync(`${outDir}/${name}`, buf);
    console.log(`Created: ${name}`);
  }
}

main().catch(console.error);
