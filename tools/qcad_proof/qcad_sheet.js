// PROOF ONLY. QCAD Professional paper-space renderer.
// Reads a governed specification. Does not invent construction facts.

include("scripts/simple.js");

var SPEC = null;
var DOC = null;
var DI = null;
var LAYERS = {};
var LINETYPES = {};
var LOG_PATH = "";
var CURRENT_BLOCK = "";

function proofLog(message) {
    if (!LOG_PATH) {
        return;
    }
    var file = new QFile(LOG_PATH);
    file.open(QIODevice.WriteOnly | QIODevice.Append | QIODevice.Text);
    var stream = new QTextStream(file);
    stream.writeString(String(message) + "\n");
    file.close();
}

function readSpec(path) {
    var file = new QFile(path);
    if (!file.open(QIODevice.ReadOnly | QIODevice.Text)) {
        throw "Cannot read specification " + path;
    }
    var stream = new QTextStream(file);
    var raw = stream.readAll();
    file.close();
    return JSON.parse(raw);
}

function envValue(name) {
    return QProcessEnvironment.systemEnvironment().value(name);
}

function addLinetype(name, description, dashes) {
    var pattern = new RLinetypePattern(false, name, description, dashes);
    var linetype = new RLinetype(DOC, pattern);
    DI.applyOperation(new RAddObjectOperation(linetype));
    LINETYPES[name] = DOC.getLinetypeId(name);
}

function addLayer(name, weight, linetypeName) {
    var linetypeId = LINETYPES[linetypeName] || DOC.getLinetypeId("CONTINUOUS");
    var layer = new RLayer(
        DOC,
        name,
        false,
        false,
        new RColor(0, 0, 0),
        linetypeId,
        weight
    );
    DI.applyOperation(new RAddObjectOperation(layer));
    LAYERS[name] = DOC.getLayerId(name);
}

function useBlock(name) {
    DI.setCurrentBlock(name);
    CURRENT_BLOCK = name;
}

function styleEntity(entity, layerName) {
    entity.setLayerId(LAYERS[layerName]);
    entity.setColor(new RColor(0, 0, 0));
    entity.setLineweight(RLineweight.WeightByLayer);
    entity.setBlockId(DOC.getBlockId(CURRENT_BLOCK));
    return entity;
}

function drawLine(x1, y1, x2, y2, layerName) {
    var entity = new RLineEntity(
        DOC,
        new RLineData(new RVector(x1, y1), new RVector(x2, y2))
    );
    DI.applyOperation(new RAddObjectOperation(styleEntity(entity, layerName)));
}

function drawPolygon(points, layerName) {
    var operation = new RAddObjectsOperation();
    var count = points.length;
    var index;
    for (index = 0; index < count; index += 1) {
        var next = points[(index + 1) % count];
        var entity = new RLineEntity(
            DOC,
            new RLineData(
                new RVector(points[index][0], points[index][1]),
                new RVector(next[0], next[1])
            )
        );
        operation.addObject(styleEntity(entity, layerName));
    }
    DI.applyOperation(operation);
}

function drawCircle(center, radius, layerName) {
    var entity = new RCircleEntity(DOC, new RCircleData(new RVector(center[0], center[1]), radius));
    DI.applyOperation(new RAddObjectOperation(styleEntity(entity, layerName)));
}

function drawText(x, y, height, text, layerName, hAlign, vAlign) {
    var position = new RVector(x, y);
    var data = new RTextData(
        position,
        position,
        height,
        0.0,
        vAlign,
        hAlign,
        RS.LeftToRight,
        RS.Exact,
        1.0,
        String(text),
        "Arial",
        false,
        false,
        0.0,
        false
    );
    var entity = new RTextEntity(DOC, data);
    DI.applyOperation(new RAddObjectOperation(styleEntity(entity, layerName)));
}

function drawLeader(points, layerName) {
    var data = new RLeaderData();
    var index;
    for (index = 0; index < points.length; index += 1) {
        data.appendVertex(new RVector(points[index][0], points[index][1]));
    }
    data.setArrowHead(true);
    var entity = new RLeaderEntity(DOC, data);
    DI.applyOperation(new RAddObjectOperation(styleEntity(entity, layerName)));
}

function drawHatch(points, layerName, solid) {
    var data = new RHatchData(solid, solid ? 1.0 : 1.25, Math.PI / 4.0, solid ? "SOLID" : "ANSI31");
    data.newLoop();
    var count = points.length;
    var index;
    for (index = 0; index < count; index += 1) {
        var next = points[(index + 1) % count];
        data.addBoundary(
            new RLine(
                new RVector(points[index][0], points[index][1]),
                new RVector(next[0], next[1])
            ),
            false
        );
    }
    var entity = new RHatchEntity(DOC, data);
    DI.applyOperation(new RAddObjectOperation(styleEntity(entity, layerName)));
}

function drawDimension(p1, p2, horizontal, layerName, textHeight, arrow, lineCoordinate) {
    var rotation = horizontal ? 0.0 : Math.PI / 2.0;
    var definition = horizontal
        ? new RVector((p1[0] + p2[0]) / 2.0, lineCoordinate)
        : new RVector(lineCoordinate, (p1[1] + p2[1]) / 2.0);
    var dimData = new RDimensionData(
        definition,
        definition,
        RS.VAlignMiddle,
        RS.HAlignCenter,
        RS.Exact,
        1.0,
        "",
        "Standard",
        0.0
    );
    var rotated = new RDimRotatedData(
        dimData,
        new RVector(p1[0], p1[1]),
        new RVector(p2[0], p2[1]),
        rotation
    );
    rotated.setDimtxt(textHeight);
    rotated.setDimasz(arrow);
    rotated.setDimexo(arrow * 0.45);
    rotated.setDimexe(arrow * 0.35);
    rotated.setDimtad(1);
    rotated.setDimtih(false);
    rotated.setDimlunit(4);
    rotated.setDimdec(4);
    rotated.setDimgap(arrow * 0.25);
    var entity = new RDimRotatedEntity(DOC, rotated);
    DI.applyOperation(new RAddObjectOperation(styleEntity(entity, layerName)));
}

function memberLayer(role) {
    if (role === "post") {
        return "S-POST";
    }
    if (role === "beam") {
        return "S-BEAM";
    }
    return "S-JOIST";
}

function placeMembers(members, origin, layerFor) {
    var ids = ["post-1", "beam-front", "joist-1"];
    var index;
    for (index = 0; index < ids.length; index += 1) {
        var member = members[ids[index]];
        var moved = [];
        var point;
        for (point = 0; point < member.polygon.length; point += 1) {
            moved.push([
                member.polygon[point][0] + origin[0],
                member.polygon[point][1] + origin[1]
            ]);
        }
        drawPolygon(moved, layerFor(member));
    }
}

function configureLayout() {
    var layout = DOC.queryLayout("Layout1");
    layout.setName("S-1");
    layout.setPlotPaperUnits(RLayout.Inches);
    layout.setPlotPaperSize(new RVector(17.0, 11.0));
    layout.setPlotRotation(RLayout.Zero);
    layout.setPlotType(RLayout.Layout);
    layout.setUseStandardScale(false);
    layout.setCanonicalMediaName("ANSI_B_(17.00_x_11.00_Inches)");
    layout.setPlotPaperMarginLeftMM(3.0);
    layout.setPlotPaperMarginRightMM(3.0);
    layout.setPlotPaperMarginTopMM(3.0);
    layout.setPlotPaperMarginBottomMM(3.0);
    DI.applyOperation(new RAddObjectOperation(layout));
    proofLog("layout " + DOC.queryLayout("S-1").getName());
}

function addViewport(center, width, height, scale, viewCenter, viewportId) {
    useBlock(RBlock.paperSpaceName);
    var data = new RViewportData();
    data.setCenter(new RVector(center[0], center[1]));
    data.setWidth(width);
    data.setHeight(height);
    data.setScale(scale);
    data.setViewCenter(new RVector(viewCenter[0], viewCenter[1]));
    data.setViewTarget(new RVector(0, 0));
    data.setOverall(false);
    data.setViewportId(viewportId);
    var entity = new RViewportEntity(DOC, data);
    styleEntity(entity, "G-VPRT");
    DI.applyOperation(new RAddObjectOperation(entity));
    drawLine(center[0] - width / 2.0, center[1] - height / 2.0, center[0] + width / 2.0, center[1] - height / 2.0, "G-VPRT");
    drawLine(center[0] + width / 2.0, center[1] - height / 2.0, center[0] + width / 2.0, center[1] + height / 2.0, "G-VPRT");
    drawLine(center[0] + width / 2.0, center[1] + height / 2.0, center[0] - width / 2.0, center[1] + height / 2.0, "G-VPRT");
    drawLine(center[0] - width / 2.0, center[1] + height / 2.0, center[0] - width / 2.0, center[1] - height / 2.0, "G-VPRT");
}

function paperPoint(viewport, modelPoint) {
    return [
        viewport.center[0] + (modelPoint[0] - viewport.view[0]) * viewport.scale,
        viewport.center[1] + (modelPoint[1] - viewport.view[1]) * viewport.scale
    ];
}

function drawTitleBlock(sheet) {
    useBlock(RBlock.paperSpaceName);
    var left = 0.28;
    var right = 16.72;
    var bottom = 0.16;
    var top = 1.22;
    drawLine(left, bottom, right, bottom, "G-BORD");
    drawLine(right, bottom, right, 10.82, "G-BORD");
    drawLine(right, 10.82, left, 10.82, "G-BORD");
    drawLine(left, 10.82, left, bottom, "G-BORD");
    drawLine(left, top, right, top, "G-TITL");
    var columns = [left, 7.4, 11.3, 13.7, right];
    var index;
    for (index = 1; index < columns.length - 1; index += 1) {
        drawLine(columns[index], bottom, columns[index], top, "G-TITL");
    }
    drawText(left + 0.12, 0.86, 0.16, sheet.organization_name, "G-TITL", RS.HAlignLeft, RS.VAlignMiddle);
    drawText(left + 0.12, 0.58, 0.11, sheet.project_name, "G-TITL", RS.HAlignLeft, RS.VAlignMiddle);
    drawText(left + 0.12, 0.34, 0.13, sheet.drawing_title.toUpperCase(), "G-TITL", RS.HAlignLeft, RS.VAlignMiddle);
    drawText(7.52, 0.92, 0.09, "ADDRESS", "G-ANNO", RS.HAlignLeft, RS.VAlignMiddle);
    drawText(7.52, 0.62, 0.12, sheet.address, "G-TITL", RS.HAlignLeft, RS.VAlignMiddle);
    drawText(7.52, 0.34, 0.08, sheet.document_status, "G-ANNO", RS.HAlignLeft, RS.VAlignMiddle);
    drawText(11.42, 0.92, 0.09, "SHEET", "G-ANNO", RS.HAlignLeft, RS.VAlignMiddle);
    drawText(11.42, 0.55, 0.22, "S-" + sheet.sheet_number, "G-TITL", RS.HAlignLeft, RS.VAlignMiddle);
    drawText(13.82, 0.96, 0.09, "REV " + sheet.revision, "G-TITL", RS.HAlignLeft, RS.VAlignMiddle);
    drawText(13.82, 0.70, 0.11, sheet.date, "G-TITL", RS.HAlignLeft, RS.VAlignMiddle);
    drawText(13.82, 0.40, 0.10, "SCALE " + sheet.scale_note, "G-TITL", RS.HAlignLeft, RS.VAlignMiddle);
}

function drawViewTitle(viewport, title, scaleNote) {
    useBlock(RBlock.paperSpaceName);
    var left = viewport.center[0] - viewport.width / 2.0 + 0.08;
    var top = viewport.center[1] + viewport.height / 2.0 - 0.08;
    drawText(left, top, 0.12, title, "G-ANNO", RS.HAlignLeft, RS.VAlignTop);
    drawText(left, top - 0.18, 0.09, scaleNote, "G-ANNO", RS.HAlignLeft, RS.VAlignTop);
}

function buildDetailBlock(detail, origin) {
    if (detail.refused) {
        return;
    }
    var block = new RBlock(DOC, detail.block_name, new RVector(0, 0));
    DI.applyOperation(new RAddObjectOperation(block));
    useBlock(detail.block_name);
    drawPolygon(detail.post.polygon, "S-POST");
    drawPolygon(detail.beam.polygon, "S-BEAM");
    if (detail.plate) {
        drawPolygon(detail.plate.polygon, "S-CONN");
        drawHatch(detail.plate.polygon, "S-HATCH", true);
        var boltIndex;
        for (boltIndex = 0; boltIndex < detail.plate.bolts.length; boltIndex += 1) {
            var bolt = detail.plate.bolts[boltIndex];
            drawCircle(bolt.center, bolt.diameter_in / 2.0, "S-CONN");
        }
        var platePoint = detail.plate.polygon[0];
        drawLeader([[platePoint[0], platePoint[1]], [16.6, 27.2]], "A-LEAD");
        drawText(16.7, 27.35, 0.18, detail.plate.connector.toUpperCase(), "A-ANNO", RS.HAlignLeft, RS.VAlignBottom);
        if (detail.plate.uncertainty) {
            drawText(16.7, 26.95, 0.13, detail.plate.uncertainty, "A-ANNO", RS.HAlignLeft, RS.VAlignTop);
        }
        if (detail.plate.bolts.length) {
            var boltCenter = detail.plate.bolts[0].center;
            drawLeader([[boltCenter[0], boltCenter[1]], [16.6, 21.4]], "A-LEAD");
            drawText(16.7, 21.4, 0.16, detail.plate.fastener.toUpperCase(), "A-ANNO", RS.HAlignLeft, RS.VAlignMiddle);
        }
    } else {
        drawText(16.4, 27.0, 0.18, "CONNECTOR GEOMETRY IS NOT SUPPLIED.", "A-ANNO", RS.HAlignLeft, RS.VAlignMiddle);
    }
    drawText(16.4, 18.4, 0.18, detail.post.id.toUpperCase(), "A-ANNO", RS.HAlignLeft, RS.VAlignMiddle);
    drawText(16.4, 31.6, 0.18, detail.beam.id.toUpperCase(), "A-ANNO", RS.HAlignLeft, RS.VAlignMiddle);
    drawText(8.1, 34.6, 0.2, detail.kind.toUpperCase() + "  " + detail.relationship_id, "A-ANNO", RS.HAlignLeft, RS.VAlignMiddle);
    var textData = new RTextData(
        new RVector(6.2, 34.7),
        new RVector(6.2, 34.7),
        0.01,
        0.0,
        RS.VAlignBottom,
        RS.HAlignLeft,
        RS.LeftToRight,
        RS.Exact,
        1.0,
        detail.relationship_id,
        "Arial",
        false,
        false,
        0.0,
        false
    );
    try {
        var attribute = new RAttributeDefinitionEntity(
            DOC,
            new RAttributeDefinitionData(textData, "RELATIONSHIP", "Stored relationship")
        );
        DI.applyOperation(new RAddObjectOperation(styleEntity(attribute, "A-ANNO")));
        proofLog("attribute RELATIONSHIP");
    } catch (attributeError) {
        proofLog("attribute skipped " + attributeError);
    }
    if (SPEC.dimensions.bearing) {
        var bearing = SPEC.dimensions.bearing;
        drawDimension(bearing.p1, bearing.p2, true, "A-DIMS", 0.2, 0.16, bearing.p1[1] + 11.0);
    }
    useBlock(RBlock.modelSpaceName);
    var reference = new RBlockReferenceEntity(
        DOC,
        new RBlockReferenceData(
            DOC.getBlockId(detail.block_name),
            new RVector(origin[0], origin[1]),
            new RVector(1, 1),
            0.0
        )
    );
    reference.setLayerId(LAYERS["S-POST"]);
    reference.setBlockId(DOC.getBlockId(RBlock.modelSpaceName));
    DI.applyOperation(new RAddObjectOperation(reference));
    proofLog("block " + detail.block_name);
}

function drawSheet() {
    var planOrigin = [0, 0];
    var elevationOrigin = [0, -400];
    var sectionOrigin = [0, -1600];
    var detailOrigin = [0, -800];

    useBlock(RBlock.modelSpaceName);
    placeMembers(SPEC.plan, planOrigin, function (member) { return memberLayer(member.role); });
    placeMembers(SPEC.elevation, elevationOrigin, function (member) { return memberLayer(member.role); });

    var cutIds = ["post-1", "beam-front", "joist-1"];
    var index;
    for (index = 0; index < cutIds.length; index += 1) {
        var member = SPEC.elevation[cutIds[index]];
        var moved = [];
        var point;
        for (point = 0; point < member.polygon.length; point += 1) {
            moved.push([
                member.polygon[point][0] + sectionOrigin[0],
                member.polygon[point][1] + sectionOrigin[1]
            ]);
        }
        drawHatch(moved, "S-HATCH", false);
        drawPolygon(moved, "S-CUT");
    }
    if (!SPEC.detail.refused && SPEC.detail.plate) {
        var plate = [];
        for (index = 0; index < SPEC.detail.plate.polygon.length; index += 1) {
            plate.push([
                SPEC.detail.plate.polygon[index][0] + sectionOrigin[0],
                SPEC.detail.plate.polygon[index][1] + sectionOrigin[1]
            ]);
        }
        drawHatch(plate, "S-HATCH", true);
        drawPolygon(plate, "S-CONN");
        for (index = 0; index < SPEC.detail.plate.bolts.length; index += 1) {
            var bolt = SPEC.detail.plate.bolts[index];
            drawCircle(
                [bolt.center[0] + sectionOrigin[0], bolt.center[1] + sectionOrigin[1]],
                bolt.diameter_in / 2.0,
                "S-CONN"
            );
        }
    }

    var beam = SPEC.dimensions.beam_length;
    drawDimension(beam.p1, beam.p2, true, "A-DIMS", 4.0, 2.4, -14);
    var joist = SPEC.dimensions.joist_length;
    drawDimension(joist.p1, joist.p2, false, "A-DIMS", 4.0, 2.4, 148);
    var post = SPEC.dimensions.post_height;
    drawDimension(
        [post.p1[0] + elevationOrigin[0], post.p1[1] + elevationOrigin[1]],
        [post.p2[0] + elevationOrigin[0], post.p2[1] + elevationOrigin[1]],
        false,
        "A-DIMS",
        1.5,
        1.0,
        elevationOrigin[0] + post.p1[0] - 6
    );

    drawText(9, 18, 4.2, SPEC.labels["post-1"], "A-ANNO", RS.HAlignLeft, RS.VAlignBottom);
    drawText(24, 16, 4.2, SPEC.labels["beam-front"], "A-ANNO", RS.HAlignLeft, RS.VAlignBottom);
    drawText(20, 28, 4.2, SPEC.labels["joist-1"], "A-ANNO", RS.HAlignLeft, RS.VAlignBottom);
    drawText(elevationOrigin[0] + 22, elevationOrigin[1] + 12, 1.6, SPEC.labels["post-1"], "A-ANNO", RS.HAlignLeft, RS.VAlignMiddle);
    drawText(elevationOrigin[0] + 28, elevationOrigin[1] + 28, 1.6, SPEC.labels["beam-front"], "A-ANNO", RS.HAlignLeft, RS.VAlignMiddle);
    drawText(elevationOrigin[0] + 20, elevationOrigin[1] + 42, 1.6, SPEC.labels["joist-1"], "A-ANNO", RS.HAlignLeft, RS.VAlignBottom);

    if (SPEC.relationships.beam_supports_joist_id) {
        var joistPolygon = SPEC.elevation["joist-1"].polygon;
        var joistX = 0;
        var joistBottom = joistPolygon[0][1];
        var joistPoint;
        for (joistPoint = 0; joistPoint < joistPolygon.length; joistPoint += 1) {
            joistX += joistPolygon[joistPoint][0];
            if (joistPolygon[joistPoint][1] < joistBottom) {
                joistBottom = joistPolygon[joistPoint][1];
            }
        }
        joistX = joistX / joistPolygon.length;
        drawLeader(
            [
                [elevationOrigin[0] + joistX, elevationOrigin[1] + joistBottom],
                [elevationOrigin[0] + 28, elevationOrigin[1] + 44],
                [elevationOrigin[0] + 36, elevationOrigin[1] + 44]
            ],
            "A-LEAD"
        );
        drawText(
            elevationOrigin[0] + 36.3,
            elevationOrigin[1] + 44.2,
            0.7,
            SPEC.relationships.joist_callout.toUpperCase(),
            "A-ANNO",
            RS.HAlignLeft,
            RS.VAlignBottom
        );
        if (!SPEC.relationships.joist_connector_geometry_supplied) {
            drawText(
                elevationOrigin[0] + 36.3,
                elevationOrigin[1] + 43.2,
                0.55,
                "CONNECTOR GEOMETRY IS NOT SUPPLIED.",
                "A-ANNO",
                RS.HAlignLeft,
                RS.VAlignTop
            );
        }
    }

    buildDetailBlock(SPEC.detail, detailOrigin);

    var planView = {
        center: [2.825, 8.45],
        width: 5.05,
        height: 4.60,
        scale: 0.03125,
        view: [80, 53]
    };
    var elevationView = {
        center: [2.825, 3.65],
        width: 5.05,
        height: 4.60,
        scale: 0.083333,
        view: [24, elevationOrigin[1] + 21]
    };
    var sectionView = {
        center: [8.075, 6.05],
        width: 5.15,
        height: 9.40,
        scale: 0.25,
        view: [15, sectionOrigin[1] + 30]
    };
    var detailView = {
        center: [13.725, 6.05],
        width: 5.85,
        height: 9.40,
        scale: 0.5,
        view: [13, detailOrigin[1] + 26]
    };

    addViewport(planView.center, planView.width, planView.height, planView.scale, planView.view, 2);
    addViewport(elevationView.center, elevationView.width, elevationView.height, elevationView.scale, elevationView.view, 3);
    addViewport(sectionView.center, sectionView.width, sectionView.height, sectionView.scale, sectionView.view, 4);
    addViewport(detailView.center, detailView.width, detailView.height, detailView.scale, detailView.view, 5);

    drawViewTitle(planView, "FRAMING PLAN", "3/8\" = 1'-0\"");
    drawViewTitle(elevationView, "ELEVATION", "1\" = 1'-0\"");
    drawViewTitle(sectionView, "SECTION A", "3\" = 1'-0\"");
    if (SPEC.detail.refused) {
        useBlock(RBlock.paperSpaceName);
        drawText(detailView.center[0], detailView.center[1], 0.16, SPEC.detail.message, "G-ANNO", RS.HAlignCenter, RS.VAlignMiddle);
        drawViewTitle(detailView, "POST / BEAM", "RELATIONSHIP NOT SUPPLIED");
    } else {
        drawViewTitle(detailView, "DETAIL 1", "6\" = 1'-0\"");
        if (SPEC.detail.plate && SPEC.detail.plate.bolts.length && SPEC.detail.plate.thickness_in < SPEC.detail.plate.bolts[0].diameter_in) {
            drawText(
                detailView.center[0],
                detailView.center[1] - detailView.height / 2.0 + 0.22,
                0.07,
                "SUPPLIED BOLT DIAMETER IS LARGER THAN SUPPLIED PLATE THICKNESS.",
                "G-ANNO",
                RS.HAlignCenter,
                RS.VAlignMiddle
            );
        }
    }

    useBlock(RBlock.paperSpaceName);
    var cutY = paperPoint(planView, [0, SPEC.section.location_in]);
    var cutStart = paperPoint(planView, [0, SPEC.section.location_in]);
    var cutEnd = paperPoint(planView, [140, SPEC.section.location_in]);
    drawLine(cutStart[0], cutStart[1], cutEnd[0], cutEnd[1], "A-ANNO");
    drawCircle([cutStart[0] - 0.16, cutY[1]], 0.12, "A-ANNO");
    drawCircle([cutEnd[0] + 0.16, cutY[1]], 0.12, "A-ANNO");
    drawText(cutStart[0] - 0.16, cutY[1], 0.10, "A", "G-ANNO", RS.HAlignCenter, RS.VAlignMiddle);
    drawText(cutEnd[0] + 0.16, cutY[1], 0.10, "A", "G-ANNO", RS.HAlignCenter, RS.VAlignMiddle);

    var postPaper = paperPoint(planView, [12, 12]);
    drawCircle([postPaper[0] + 0.42, postPaper[1] + 0.28], 0.12, "A-ANNO");
    drawText(postPaper[0] + 0.42, postPaper[1] + 0.28, 0.10, "1", "G-ANNO", RS.HAlignCenter, RS.VAlignMiddle);
    drawLeader(
        [
            [postPaper[0] + 0.08, postPaper[1] + 0.08],
            [postPaper[0] + 0.32, postPaper[1] + 0.22]
        ],
        "A-LEAD"
    );
    proofLog("viewports 4");
}

function main() {
    LOG_PATH = envValue("QCAD_PROOF_LOG");
    try {
        var specPath = envValue("QCAD_PROOF_SPEC");
        var dxfPath = envValue("QCAD_PROOF_DXF");
        SPEC = readSpec(specPath);
        proofLog("spec " + SPEC.member_ids.join(","));
        var storage = new RMemoryStorage();
        var index = new RSpatialIndexNavel();
        DOC = new RDocument(storage, index);
        DI = new RDocumentInterface(DOC);
        CURRENT_BLOCK = RBlock.modelSpaceName;
        DOC.setUnit(RS.Inch);
        DOC.setLinearFormat(RS.Architectural);
        addLinetype("HIDDEN", "Hidden", [0.25, -0.125]);
        addLinetype("DASHED", "Dashed", [0.5, -0.25]);
        addLayer("S-POST", RLineweight.Weight050, "CONTINUOUS");
        addLayer("S-BEAM", RLineweight.Weight050, "CONTINUOUS");
        addLayer("S-JOIST", RLineweight.Weight040, "CONTINUOUS");
        addLayer("S-CUT", RLineweight.Weight070, "CONTINUOUS");
        addLayer("S-HATCH", RLineweight.Weight013, "CONTINUOUS");
        addLayer("S-CONN", RLineweight.Weight035, "CONTINUOUS");
        addLayer("S-HIDN", RLineweight.Weight018, "HIDDEN");
        addLayer("A-DIMS", RLineweight.Weight018, "CONTINUOUS");
        addLayer("A-ANNO", RLineweight.Weight018, "CONTINUOUS");
        addLayer("A-LEAD", RLineweight.Weight018, "CONTINUOUS");
        addLayer("G-TITL", RLineweight.Weight050, "CONTINUOUS");
        addLayer("G-BORD", RLineweight.Weight040, "CONTINUOUS");
        addLayer("G-ANNO", RLineweight.Weight018, "CONTINUOUS");
        addLayer("G-VPRT", RLineweight.Weight025, "CONTINUOUS");
        configureLayout();
        drawTitleBlock(SPEC.sheet);
        drawSheet();
        DI.exportFile(dxfPath);
        proofLog("exported " + dxfPath);
    } catch (error) {
        proofLog("ERR " + error);
    }
    QCoreApplication.exit(0);
}

main();
