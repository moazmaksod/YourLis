

/****** Object:  StoredProcedure [dbo].[GetPatientCBCResult]    Script Date: 8/15/2025 10:41:22 PM ******/
SET ANSI_NULLS ON
GO

SET QUOTED_IDENTIFIER ON
GO


DROP PROCEDURE IF EXISTS [dbo].[GetPatientCBCResult];
GO

CREATE OR ALTER PROCEDURE [dbo].[GetPatientCBCResult]
    @PATIENT_ID VARCHAR(13)  -- Patient ID is required
AS
BEGIN
    SET NOCOUNT ON;

    -- Fetch patient details and CBC results
    SELECT 
        -- Patient Information
        p.patientid AS [Patient ID],
        p.patientnamear AS [Name],
        p.patientage AS [Age],
        p.patientageunit AS [Age Unit],
        p.patientsex AS [Gender],

        -- CBC Test Details
        c.requestdate AS [Requested Date],

        c.hgb AS [Hemoglobin (HGB)],

        c.rbc AS [Red Blood Cells (RBC)],
			c.hct AS [Hematocrit (HCT)],
			c.mcv AS [Mean Corpuscular Volume (MCV)],
			c.mch AS [Mean Corpuscular Hemoglobin (MCH)],
			c.mchc AS [Mean Corpuscular Hemoglobin Concentration (MCHC)],
			c.rdw AS [Red Cell Distribution Width (RDW)],

		c.plt AS [Platelets (PLT)],
			c.pct AS [Plateletcrit (PCT)],
			c.mpv AS [Mean Platelet Volume (MPV)],
			c.pdw AS [Platelet Distribution Width (PDW)],

		c.wbc AS [White Blood Cells (WBC)],
			c.neut AS [Neutrophils],
			c.lymph AS [Lymphocytes],
			c.mono AS [Monocytes],
			c.eosino AS [Eosinophils],
			c.baso AS [Basophils]
			-- ,c.othercell AS [Other Cells]
			-- ,c.seg AS [Segmented Neutrophils]
		   -- , c.bandx AS [Band Neutrophils]
			-- ,c.Juvenile AS [Juvenile Cells]
		   -- , c.Myelocytes AS [Myelocytes]
		   -- , c.Promyelocyte AS [Promyelocytes]
		   -- , c.Blast AS [Blasts]
		  -- ,  c.NRBCWBC AS [Nucleated RBCs]
      -- ,  c.comment AS [Comment]

    FROM 
        patientinfo p
    LEFT JOIN 
        cbc c ON p.patientid = c.patientid
    WHERE 
        p.patientid = @PATIENT_ID
    ORDER BY 
        c.requestdate DESC;  -- Show the latest test first
END;
GO


