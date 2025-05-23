USE [patients]
GO

/****** Object:  StoredProcedure [dbo].[GetPatientInfo]    Script Date: 5/23/2025 1:25:30 AM ******/
SET ANSI_NULLS ON
GO

SET QUOTED_IDENTIFIER ON
GO

CREATE PROCEDURE [dbo].[GetPatientInfo]
    @PATIENT_ID VARCHAR(13) = NULL,
    @PATIENT_NAME NVARCHAR(100) = NULL,
    @START_DATE SMALLDATETIME = NULL,  -- Parameter for start date
    @END_DATE SMALLDATETIME = NULL,     -- Parameter for end date
    @RESULT_FINISHED BIT = NULL 
AS
BEGIN
    SET NOCOUNT ON;

    DECLARE @SQL NVARCHAR(MAX);
    DECLARE @Params NVARCHAR(MAX);
    
    SET @SQL = '
    SELECT 
        p.patientid AS [Patient ID],
        p.patientnamear AS [Name],
        p.patientage AS [Age],
        p.patientageunit AS [Age Unit],
        p.patientsex AS [Gender],
        pt.requestdate AS [Requested Date],
        CASE 
            WHEN pt.testcode = 56 THEN ''CBC''
            WHEN pt.testcode = 50 THEN ''Hgb''
            ELSE ''Unknown Test''
        END AS [Requested Test],
        CASE 
            WHEN pt.resultfinsh = 0 THEN ''Pending''
            ELSE ''Completed''
        END AS [Result State] 
    FROM 
        patientinfo p
    JOIN 
        patienttest pt ON p.patientid = pt.patientid 
    WHERE 
        pt.testcode IN (56, 50)';

    -- Dynamically add filters based on parameters provided
    IF (@PATIENT_ID IS NOT NULL AND @PATIENT_ID <> '' AND @PATIENT_NAME IS NULL)
    BEGIN
        SET @SQL = @SQL + ' AND p.patientid LIKE ''%'' + @PatientID + ''%''';
    END

    IF (@PATIENT_NAME IS NOT NULL AND @PATIENT_NAME <> '' AND @PATIENT_ID IS NULL)
    BEGIN
        SET @SQL = @SQL + ' AND p.patientnamear LIKE ''%'' + @PatientName + ''%''';
    END

    IF (@PATIENT_NAME IS NOT NULL AND @PATIENT_NAME <> '' AND @PATIENT_ID IS NOT NULL AND @PATIENT_ID <> '')
    BEGIN
        SET @SQL = @SQL + ' AND (p.patientid LIKE ''%'' + @PatientID + ''%'' OR p.patientnamear LIKE ''%'' + @PatientName + ''%'')';
    END

    -- Add conditions for date range search based on provided dates
    IF @START_DATE IS NOT NULL AND @END_DATE IS NOT NULL
    BEGIN
        SET @SQL = @SQL + ' AND pt.requestdate BETWEEN @StartDate AND @EndDate';
    END
    ELSE IF @START_DATE IS NOT NULL
    BEGIN
        SET @SQL = @SQL + ' AND pt.requestdate >= @StartDate';  -- Only start date provided
    END
    ELSE IF @END_DATE IS NOT NULL
    BEGIN
        SET @SQL = @SQL + ' AND pt.requestdate <= @EndDate';     -- Only end date provided
    END

    -- Check for the result finished status
    IF @RESULT_FINISHED IS NOT NULL 
    BEGIN
        SET @SQL = @SQL + ' AND pt.resultfinsh = @ResultFinished';
    END

	SET @SQL = @SQL + ' ORDER BY pt.requestdate ASC';

    -- Define parameter types for sp_executesql
    SET @Params = N'@PatientID VARCHAR(13), @PatientName NVARCHAR(100), @StartDate SMALLDATETIME, @EndDate SMALLDATETIME, @ResultFinished BIT';

    -- Execute the dynamic SQL
    EXEC sp_executesql @SQL, @Params, 
                       @PatientID = @PATIENT_ID, 
                       @PatientName = @PATIENT_NAME, 
                       @StartDate = @START_DATE,   -- Pass start date
                       @EndDate = @END_DATE,       -- Pass end date
                       @ResultFinished = @RESULT_FINISHED;
END;
GO


