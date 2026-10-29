# main.py
from fastapi import FastAPI, Depends, Request, Form
from fastapi.responses import HTMLResponse,RedirectResponse
from fastapi.templating import Jinja2Templates
from db import getDB,lifespan
from fastapi.staticfiles import StaticFiles

#from routes import router as all_routes
#from routes.upload import router as upload_router
#from routes import users
templates = Jinja2Templates(directory="templates")
app = FastAPI(lifespan=lifespan)

from starlette.middleware.sessions import SessionMiddleware
app.add_middleware(
	SessionMiddleware,
	secret_key="your-secret-key",
	max_age=None, #86400,  # 1 day
	same_site="lax",  # Options: 'lax', 'strict', 'none'
	https_only=False,  # Set to True in production with HTTPS,
)
# Include the router
from routes.login import router as loginRoute #取個別名避免同名變數衝突
app.include_router(loginRoute, prefix="/user") #mount every thing from ./routes/ to url under prefix

def chkLogin():
	def checker(request: Request): #fastAPI will auto-inject request to dependency function
		loginUser = request.session.get("user") #get identity from session
		if loginUser:
			return loginUser #return whatever you need
		else:
			#raise HTTPException(status_code=403, detail="Forbidden")
			return None
	return checker
       
@app.get("/")
async def home(request: Request, user=Depends(chkLogin())):
	print(user)
	if user is None:
		return RedirectResponse(url="/w/login.html", status_code=302)
	else:
		return HTMLResponse(f"Welcome {user}! <a href='/user/logout'>logout</a>")

@app.get("/students/list")
async def read_users(db=Depends(getDB)):
	cur=await db.execute("SELECT * FROM students")
	return await cur.fetchall()

@app.get("/students/list/template")
async def stuList(request:Request, db=Depends(getDB)):
	cur=await db.execute("SELECT * FROM students order by stuid;")
	data= await cur.fetchall()
	return templates.TemplateResponse(name="studentList.html", request=request,context={"students": data})

@app.get("/student/create")
async def stuCreateForm(request: Request):
    return templates.TemplateResponse(name="studentCreate.html", request=request)
@app.post("/student/create")
async def stuCreate(
    dept: str = Form(...),
    stuid: int = Form(...),
    name: str = Form(...),
    id: str = Form(...),
    height: float = Form(...),
    weight: float = Form(...),
    math: int = Form(...),
    english: int = Form(...),
    chinese: int = Form(...),
    birthday: str = Form(...),
    iq: int = Form(...),
    city: str = Form(...),
    mentor: str = Form(...),
    db = Depends(getDB)
):
    await db.execute(
        """INSERT INTO students (dept, stuid, name, id, height, weight, math, english, chinese, birthday, iq, city, mentor) 
           VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)""", 
        (dept, stuid, name, id, height, weight, math, english, chinese, birthday, iq, city, mentor)
    )
    await db.commit()
    # Use 303 status code so the browser switches from POST to GET on redirect
    return RedirectResponse(url="/students/list/template", status_code=303)

@app.get("/student/edit/{stuid}")
async def stuEdit(stuid:int,request:Request, db=Depends(getDB)):
	cur=await db.execute("SELECT * FROM students where stuid=%s",(stuid,))
	data= await cur.fetchone()
	return templates.TemplateResponse(name="studentEdit.html", request=request,context={"data": data})

@app.get("/student/delete/{stuid}")
async def stuDelete(stuid: int, db = Depends(getDB)):
    await db.execute("DELETE FROM students WHERE stuid = %s", (stuid,))
    await db.commit()
    return RedirectResponse(url="/students/list/template", status_code=303)

#@app.post("/student/update")
#async def stuUpdate(stuid:int=Form(...), name:str=Form(...), height:int=Form(...), db=Depends(getDB)):
	#print(stuid, name, height)
	#await db.execute("update students set name=%s, height=%s where stuid=%s;", (name, height, stuid))
	#return RedirectResponse(url="/students/list/template",status_code=303) #use 303 to switch to GET

#定義靜態網頁的目錄
app.mount("/w", StaticFiles(directory="www"))
